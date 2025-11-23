
# server/messaging/management/commands/clear_and_rebuild.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import RAGChunk
from messaging.rag_service import rag_service
from documents.models import Document

class Command(BaseCommand):
    help = 'clear all rag data and rebuild from scratch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='rebuild for specific user only',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='confirm destructive operation',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.ERROR(
                    'this will delete all rag data and rebuild. use --confirm to proceed'
                )
            )
            return

        self.stdout.write(self.style.WARNING('=== Clear and Rebuild RAG Data ===\n'))

        if options['user_id']:
            self._rebuild_user(options['user_id'])
        else:
            self._rebuild_all()

    def _rebuild_user(self, user_id):
        """rebuild rag data for specific user"""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"user {user_id} not found"))
            return

        self.stdout.write(f"👤 rebuilding rag data for: {user.username}")

        # clear existing data
        deleted_count = RAGChunk.objects.filter(user=user).delete()[0]
        self.stdout.write(f"🗑️ deleted {deleted_count} existing chunks")

        # rebuild profile
        self.stdout.write("🔄 embedding profile...")
        profile_result = rag_service.embed_user_profile(user)
        if profile_result['success']:
            self.stdout.write("   ✅ profile embedded")
        else:
            self.stdout.write(f"   ❌ profile failed: {profile_result['error']}")

        # rebuild documents
        documents = Document.objects.filter(user=user, status='completed')
        if documents.exists():
            self.stdout.write(f"🔄 embedding {documents.count()} documents...")
            for doc in documents:
                doc_result = rag_service.embed_document(user, doc)
                if doc_result['success']:
                    self.stdout.write(f"   ✅ {doc.title} ({doc_result['chunks_created']} chunks)")
                else:
                    self.stdout.write(f"   ❌ {doc.title} failed: {doc_result['error']}")

        # final stats
        final_count = RAGChunk.objects.filter(user=user).count()
        self.stdout.write(self.style.SUCCESS(f"✅ rebuild complete: {final_count} total chunks"))

    def _rebuild_all(self):
        """rebuild rag data for all users"""
        self.stdout.write("🔄 rebuilding rag data for ALL users...")

        # clear all data
        total_deleted = RAGChunk.objects.all().delete()[0]
        self.stdout.write(f"🗑️ deleted {total_deleted} existing chunks")

        # rebuild for all users
        users = User.objects.all()
        for user in users:
            self.stdout.write(f"\n👤 rebuilding for {user.username}...")
            self._rebuild_user(user.id)