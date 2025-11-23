# server/users/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import AcademicInfo, Preferences, UserProfile
from messaging.rag_service import rag_service
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=AcademicInfo)
def auto_embed_academic_profile(sender, instance, created, **kwargs):
    """automatically re-embed user profile when academic info changes"""
    try:
        logger.info(f"🔄 auto-embedding profile after academic update for user {instance.user.id}")
        result = rag_service.embed_user_profile(instance.user)

        if result['success']:
            logger.info(f"✅ profile re-embedded after academic update")
        else:
            logger.warning(f"⚠️ profile re-embedding failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"❌ profile re-embedding error: {e}")


@receiver(post_save, sender=Preferences)
def auto_embed_preferences_profile(sender, instance, created, **kwargs):
    """automatically re-embed user profile when preferences change"""
    try:
        logger.info(f"🔄 auto-embedding profile after preferences update for user {instance.user.id}")
        result = rag_service.embed_user_profile(instance.user)

        if result['success']:
            logger.info(f"✅ profile re-embedded after preferences update")
        else:
            logger.warning(f"⚠️ profile re-embedding failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"❌ profile re-embedding error: {e}")


@receiver(post_save, sender=User)
def auto_embed_user_profile(sender, instance, created, **kwargs):
    """automatically embed user profile when basic user info changes"""
    # skip on user creation - wait for profile completion
    if created:
        return

    # only re-embed if first_name or last_name changed
    if hasattr(instance, '_state') and instance._state.adding:
        return

    try:
        # check if user has basic profile info
        if not (instance.first_name or instance.last_name):
            return

        logger.info(f"🔄 auto-embedding profile after user update for user {instance.id}")
        result = rag_service.embed_user_profile(instance)

        if result['success']:
            logger.info(f"✅ profile re-embedded after user update")
        else:
            logger.warning(f"⚠️ profile re-embedding failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"❌ profile re-embedding error: {e}")


@receiver(post_delete, sender=User)
def cleanup_user_embeddings(sender, instance, **kwargs):
    """clean up all user embeddings when user is deleted"""
    try:
        result = rag_service.clear_user_data(instance)
        if result:
            logger.info(f"🗑️ cleaned up all rag data for deleted user {instance.id}")

    except Exception as e:
        logger.error(f"❌ error cleaning up embeddings for user {instance.id}: {e}")