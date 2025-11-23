# quick check command to see your current model structure
# server/messaging/management/commands/check_model.py
from django.core.management.base import BaseCommand
from core.models import RAGChunk

class Command(BaseCommand):
    help = 'check rag chunk model structure'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== RAG Model Structure ===\n'))

        # show model fields
        fields = [f.name for f in RAGChunk._meta.get_fields()]
        self.stdout.write(f"📋 RAGChunk model fields:")
        for field in fields:
            self.stdout.write(f"   - {field}")

        # check a sample chunk if any exist
        sample_chunk = RAGChunk.objects.first()
        if sample_chunk:
            self.stdout.write(f"\n📄 sample chunk:")
            self.stdout.write(f"   id: {sample_chunk.id}")
            self.stdout.write(f"   user: {sample_chunk.user.username}")
            self.stdout.write(f"   type: {sample_chunk.chunk_type}")

            # check embedding field type
            try:
                embedding = sample_chunk.embedding
                if embedding:
                    self.stdout.write(f"   embedding type: {type(embedding)}")
                    if isinstance(embedding, list):
                        self.stdout.write(f"   embedding dimensions: {len(embedding)}")
                    elif isinstance(embedding, str):
                        # might be json string
                        import json
                        try:
                            parsed = json.loads(embedding)
                            if isinstance(parsed, list):
                                self.stdout.write(f"   embedding (parsed from json): {len(parsed)} dimensions")
                        except:
                            self.stdout.write(f"   embedding string length: {len(embedding)}")
                else:
                    self.stdout.write(f"   embedding: None")
            except Exception as e:
                self.stdout.write(f"   embedding error: {e}")
        else:
            self.stdout.write("\n⚠️ no chunks found in database")
