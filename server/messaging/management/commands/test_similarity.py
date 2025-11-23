
# server/messaging/management/commands/test_similarity.py
from django.core.management.base import BaseCommand
from core.services.embedding_service import embedding_service

class Command(BaseCommand):
    help = 'test similarity calculation in isolation'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Testing Similarity Calculation ===\n'))

        try:
            # generate two test embeddings
            self.stdout.write("🔤 generating test embeddings...")

            result1 = embedding_service.generate_embedding("hello world")
            result2 = embedding_service.generate_embedding("hello there")

            embedding1 = result1['embedding']
            embedding2 = result2['embedding']

            self.stdout.write(f"✅ embedding 1: {len(embedding1)} dimensions")
            self.stdout.write(f"✅ embedding 2: {len(embedding2)} dimensions")

            # test similarity
            similarity = embedding_service.calculate_similarity(embedding1, embedding2)
            self.stdout.write(f"✅ similarity: {similarity}")

            # test with identical embeddings
            self_similarity = embedding_service.calculate_similarity(embedding1, embedding1)
            self.stdout.write(f"✅ self-similarity: {self_similarity} (should be 1.0)")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ similarity test failed: {e}"))