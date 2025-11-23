from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from messaging.models import Document  # adjust if your model is named differently
from messaging.rag_service import rag_service
from pprint import pprint


class Command(BaseCommand):
    help = "Embed all user profiles and documents, then show in-memory chunks"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Starting profile embedding...")
        users = User.objects.all()
        for user in users:
            result = rag_service.embed_user_profile(user)
            if result['success']:
                self.stdout.write(f"✅ Profile embedded for user {user.id}")
            else:
                self.stdout.write(f"⚠️ Profile embedding failed for user {user.id}: {result['error']}")

        self.stdout.write("📄 Starting document embedding...")
        documents = Document.objects.filter(status='completed')  # adjust filter if needed
        for doc in documents:
            result = rag_service.embed_document(doc.user, doc)
            if result['success']:
                self.stdout.write(f"✅ Document {doc.id} embedded ({result['chunks_created']} chunks)")
            else:
                self.stdout.write(f"⚠️ Document embedding failed for {doc.id}: {result['error']}")

        self.stdout.write("\n📦 Dumping all in-memory chunks by user:\n")

        for user_id, chunks in rag_service.chunks.items():
            print(f"👤 User {user_id} — {len(chunks)} chunks")
            for chunk in chunks:
                pprint({
                    'id': chunk.id,
                    'type': chunk.type,
                    'source': chunk.source,
                    'content': chunk.content[:100] + '...' if len(chunk.content) > 100 else chunk.content,
                    'embedding_dim': len(chunk.embedding),
                    'metadata': chunk.metadata,
                })
            print('-' * 40)
