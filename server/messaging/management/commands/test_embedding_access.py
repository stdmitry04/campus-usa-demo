# server/messaging/management/commands/test_embedding_access.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import RAGChunk
from core.services.embedding_service import embedding_service
import json

class Command(BaseCommand):
    help = 'test embedding property access in detail'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            required=True,
            help='user id to test',
        )

    def handle(self, *args, **options):
        user_id = options['user_id']

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"user {user_id} not found"))
            return

        self.stdout.write(self.style.SUCCESS('=== Test Embedding Property Access ===\n'))

        chunk = RAGChunk.objects.filter(user=user).first()
        if not chunk:
            self.stdout.write(self.style.WARNING("no chunks found for user"))
            return

        self.stdout.write(f"📄 testing chunk: {chunk.id}")

        # test 1: check model fields
        self.stdout.write(f"\n🔍 model fields:")
        for field in RAGChunk._meta.get_fields():
            self.stdout.write(f"   {field.name}: {type(field).__name__}")

        # test 2: check what exists on the instance
        self.stdout.write(f"\n🔍 instance attributes:")
        for attr in ['embedding', '_embedding']:
            if hasattr(chunk, attr):
                raw_value = getattr(chunk, attr)
                self.stdout.write(f"   {attr}: {type(raw_value)} (length: {len(raw_value) if hasattr(raw_value, '__len__') else 'N/A'})")
            else:
                self.stdout.write(f"   {attr}: NOT FOUND")

        # test 3: check property vs direct access
        self.stdout.write(f"\n🔍 property access test:")

        # method 1: property access
        try:
            prop_embedding = chunk.embedding
            self.stdout.write(f"   chunk.embedding: {type(prop_embedding)}")
            if isinstance(prop_embedding, list):
                self.stdout.write(f"      dimensions: {len(prop_embedding)}")
            elif isinstance(prop_embedding, str):
                self.stdout.write(f"      string length: {len(prop_embedding)}")
        except Exception as e:
            self.stdout.write(f"   chunk.embedding: ERROR - {e}")

        # method 2: direct field access (if exists)
        try:
            if hasattr(chunk, '_embedding'):
                direct_embedding = chunk._embedding
                self.stdout.write(f"   chunk._embedding: {type(direct_embedding)}")
                if isinstance(direct_embedding, str):
                    self.stdout.write(f"      string length: {len(direct_embedding)}")
                    # try to parse
                    try:
                        parsed = json.loads(direct_embedding)
                        self.stdout.write(f"      parsed type: {type(parsed)}")
                        if isinstance(parsed, list):
                            self.stdout.write(f"      parsed dimensions: {len(parsed)}")
                    except:
                        self.stdout.write(f"      failed to parse as json")
        except Exception as e:
            self.stdout.write(f"   chunk._embedding: ERROR - {e}")

        # test 4: test similarity calculation
        self.stdout.write(f"\n🔍 similarity calculation test:")

        try:
            # generate test query embedding
            query_result = embedding_service.generate_embedding("test")
            query_embedding = query_result['embedding']

            self.stdout.write(f"   query embedding: {len(query_embedding)} dimensions")

            # try to get chunk embedding for comparison
            chunk_embedding = chunk.embedding

            if isinstance(chunk_embedding, list):
                self.stdout.write(f"   chunk embedding: {len(chunk_embedding)} dimensions")

                # test similarity
                similarity = embedding_service.calculate_similarity(query_embedding, chunk_embedding)
                self.stdout.write(f"   ✅ similarity: {similarity}")
            else:
                self.stdout.write(f"   ❌ chunk embedding is not a list: {type(chunk_embedding)}")

        except Exception as e:
            self.stdout.write(f"   ❌ similarity test failed: {e}")

# Immediate fix: Update your retrieve_context method to handle string embeddings
# Add this to your rag_service.py temporarily:

def retrieve_context_fixed(self, user: User, query: str, top_k: int = 5) -> Dict:
    """retrieve relevant context with string embedding handling"""
    start_time = time.time()
    user_id = str(user.id)

    try:
        user_chunks = RAGChunk.objects.filter(user=user).exclude(_embedding__isnull=True)

        if not user_chunks.exists():
            return {
                'contexts': [],
                'has_context': False,
                'processing_time': time.time() - start_time
            }

        # generate query embedding
        query_embedding_result = self.embedding_service.generate_embedding(query)
        query_embedding = query_embedding_result['embedding']

        chunk_similarities = []

        for chunk in user_chunks:
            try:
                # get embedding and handle both string and list cases
                chunk_embedding = chunk.embedding

                # if it's still a string, try to parse it manually
                if isinstance(chunk_embedding, str):
                    try:
                        chunk_embedding = json.loads(chunk_embedding)
                    except:
                        continue

                # now it should be a list
                if isinstance(chunk_embedding, list) and len(chunk_embedding) == len(query_embedding):
                    similarity = self.embedding_service.calculate_similarity(
                        query_embedding, chunk_embedding
                    )
                    chunk_similarities.append((chunk, similarity))

            except Exception as e:
                logger.warning(f"skipping chunk {chunk.id}: {e}")
                continue

        # rest of the method stays the same...
        chunk_similarities.sort(key=lambda x: x[1], reverse=True)
        top_chunks = chunk_similarities[:top_k]

        contexts = []
        for chunk, similarity in top_chunks:
            contexts.append({
                'content': chunk.content,
                'type': chunk.chunk_type,
                'source': chunk.source,
                'similarity': similarity,
                'metadata': chunk.metadata
            })

        return {
            'contexts': contexts,
            'has_context': len(contexts) > 0,
            'processing_time': time.time() - start_time
        }

    except Exception as e:
        logger.error(f"context retrieval failed: {e}")
        return {
            'contexts': [],
            'has_context': False,
            'error': str(e),
            'processing_time': time.time() - start_time
        }