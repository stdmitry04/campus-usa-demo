# server/messaging/management/commands/embed_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from messaging.rag_service import rag_service
from core.models import RAGChunk
import time

class Command(BaseCommand):
    help = 'embed user profiles in rag system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='embed specific user profile by id',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='embed specific user profile by username',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='embed all user profiles',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='re-embed even if profile already exists',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='show what would be embedded without actually doing it',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Profile Embedding ===\n'))

        if options['user_id']:
            self._embed_user_by_id(options['user_id'], options['force'], options['dry_run'])
        elif options['username']:
            self._embed_user_by_username(options['username'], options['force'], options['dry_run'])
        elif options['all']:
            self._embed_all_users(options['force'], options['dry_run'])
        else:
            self.stdout.write(self.style.ERROR('please specify --user-id, --username, or --all'))

    def _embed_user_by_id(self, user_id, force=False, dry_run=False):
        """embed specific user by id"""
        try:
            user = User.objects.get(id=user_id)
            self._embed_single_user(user, force, dry_run)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"user with id {user_id} not found"))

    def _embed_user_by_username(self, username, force=False, dry_run=False):
        """embed specific user by username"""
        try:
            user = User.objects.get(username=username)
            self._embed_single_user(user, force, dry_run)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"user '{username}' not found"))

    def _embed_all_users(self, force=False, dry_run=False):
        """embed all user profiles"""
        users = User.objects.all()

        if not users.exists():
            self.stdout.write(self.style.WARNING("no users found"))
            return

        self.stdout.write(f"found {users.count()} users")

        if not force:
            # filter out users who already have profile embeddings
            users_with_profiles = RAGChunk.objects.filter(
                chunk_type='profile'
            ).values_list('user_id', flat=True)

            users_to_embed = users.exclude(id__in=users_with_profiles)
            self.stdout.write(f"{len(users_with_profiles)} users already have profiles")
            self.stdout.write(f"{users_to_embed.count()} users need embedding")
        else:
            users_to_embed = users
            self.stdout.write(f"force mode: will re-embed all {users_to_embed.count()} users")

        if dry_run:
            self.stdout.write(self.style.WARNING("dry run mode - no actual embedding"))
            for user in users_to_embed:
                self.stdout.write(f"would embed: {user.username} (id: {user.id})")
            return

        success_count = 0
        error_count = 0
        start_time = time.time()

        for i, user in enumerate(users_to_embed, 1):
            self.stdout.write(f"[{i}/{users_to_embed.count()}] embedding {user.username}...")

            try:
                result = rag_service.embed_user_profile(user)
                if result['success']:
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✅ embedded ({result['content_length']} chars, "
                            f"{result['processing_time']:.2f}s, "
                            f"cached: {result['cached']})"
                        )
                    )
                else:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f"  ❌ failed: {result['error']}"))
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"  ❌ exception: {e}"))

        total_time = time.time() - start_time
        self.stdout.write(f"\n📊 summary:")
        self.stdout.write(f"  ✅ successful: {success_count}")
        self.stdout.write(f"  ❌ failed: {error_count}")
        self.stdout.write(f"  ⏱️ total time: {total_time:.2f}s")
        self.stdout.write(f"  ⚡ avg per user: {total_time/max(success_count + error_count, 1):.2f}s")

    def _embed_single_user(self, user, force=False, dry_run=False):
        """embed single user profile"""
        self.stdout.write(f"👤 user: {user.username} (id: {user.id})")

        # check if profile already exists
        existing_profile = RAGChunk.objects.filter(
            user=user,
            chunk_type='profile'
        ).first()

        if existing_profile and not force:
            self.stdout.write(
                self.style.WARNING(
                    f"profile already exists (created: {existing_profile.created_at}). "
                    f"use --force to re-embed"
                )
            )
            return

        if existing_profile and force:
            self.stdout.write("force mode: will re-embed existing profile")

        if dry_run:
            self.stdout.write(self.style.WARNING("dry run mode - would embed profile"))
            return

        # embed the profile
        try:
            start_time = time.time()
            result = rag_service.embed_user_profile(user)

            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ profile embedded successfully\n"
                        f"   content length: {result['content_length']} chars\n"
                        f"   processing time: {result['processing_time']:.3f}s\n"
                        f"   model: {result['model']}\n"
                        f"   cached: {result['cached']}"
                    )
                )
            else:
                self.stdout.write(self.style.ERROR(f"❌ failed to embed profile: {result['error']}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ exception during embedding: {e}"))