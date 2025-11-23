from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from messaging.models import RAGChunk
from core.services.rag_service import rag_service
from documents.models import Document

class Command(BaseCommand):
    help = 'test embedding functionality'

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, help='user id to test')

    def handle(self, *args, **options):
        user_id = options.get('user_id')

        if user_id:
            user = User.objects.get(id=user_id)

            # test user stats
            stats = rag_service.get_user_stats(user)
            self.stdout.write(f"user {user_id} rag stats: {stats}")

            # show chunks
            chunks = RAGChunk.objects.filter(user=user)
            self.stdout.write(f"found {chunks.count()} chunks:")
            for chunk in chunks:
                self.stdout.write(f"  - {chunk.chunk_type}: {chunk.source} ({len(chunk.content)} chars)")

        try:
            doc = Document.objects.first()
            user = doc.user

            self.stdout.write(f"testing embedding for document: {doc.title}")

            # test document embedding
            result = rag_service.embed_document(user, doc)
            self.stdout.write(f"embedding result: {result}")

        except Document.DoesNotExist:
            self.stdout.write("document not found")