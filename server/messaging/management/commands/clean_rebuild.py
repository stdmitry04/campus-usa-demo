# server/messaging/management/commands/clean_rebuild.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import RAGChunk
from messaging.rag_service import rag_service
from documents.models import Document
from django.db import transaction

class Command(BaseCommand):
    help = 'clean rebuild of all rag data (nuclear option)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            required=True,
            help='user id to rebuild',
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
                    'this will delete all rag data and rebuild. use --confirm'
                )
            )
            return

        user_id = options['user_id']

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"user {user_id} not found"))
            return

        self.stdout.write(self.style.WARNING(f'=== CLEAN REBUILD for {user.username} ===\n'))

        with transaction.atomic():
            # nuclear option: delete all chunks
            self.stdout.write("💥 deleting all existing chunks...")
            deleted_count = RAGChunk.objects.filter(user=user).delete()[0]
            self.stdout.write(f"   deleted {deleted_count} chunks")

            # verify deletion
            remaining = RAGChunk.objects.filter(user=user).count()
            if remaining > 0:
                self.stdout.write(self.style.ERROR(f"   ❌ {remaining} chunks still remain!"))
                return

            # rebuild profile
            self.stdout.write("\n👤 rebuilding profile...")
            try:
                profile_result = rag_service.embed_user_profile(user)
                if profile_result['success']:
                    self.stdout.write("   ✅ profile embedded")
                else:
                    self.stdout.write(f"   ❌ profile failed: {profile_result['error']}")
            except Exception as e:
                self.stdout.write(f"   ❌ profile exception: {e}")

            # rebuild documents
            self.stdout.write("\n📄 rebuilding documents...")
            documents = Document.objects.filter(user=user, status='completed')

            for doc in documents:
                try:
                    doc_result = rag_service.embed_document(user, doc)
                    if doc_result['success']:
                        self.stdout.write(f"   ✅ {doc.title} ({doc_result['chunks_created']} chunks)")
                    else:
                        self.stdout.write(f"   ❌ {doc.title}: {doc_result['error']}")
                except Exception as e:
                    self.stdout.write(f"   ❌ {doc.title}: {e}")

            # final verification
            final_count = RAGChunk.objects.filter(user=user).count()
            self.stdout.write(f"\n✅ rebuild complete: {final_count} total chunks")

            # test access
            if final_count > 0:
                test_chunk = RAGChunk.objects.filter(user=user).first()
                try:
                    test_embedding = test_chunk.embedding
                    if isinstance(test_embedding, list):
                        self.stdout.write(f"✅ embedding access test: {len(test_embedding)} dimensions")
                    else:
                        self.stdout.write(f"❌ embedding access test: {type(test_embedding)}")
                except Exception as e:
                    self.stdout.write(f"❌ embedding access test failed: {e}")