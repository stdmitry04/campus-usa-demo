# server/messaging/management/commands/diagnose_rag.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import RAGChunk
from core.services.embedding_service import embedding_service
import json

class Command(BaseCommand):
    help = 'comprehensive rag system diagnosis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            required=True,
            help='user id to diagnose',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== COMPREHENSIVE RAG DIAGNOSIS ===\n'))

        user_id = options['user_id']

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"user {user_id} not found"))
            return

        self.stdout.write(f"👤 diagnosing user: {user.username} (id: {user.id})\n")

        # step 1: check model structure
        self._check_model_structure()

        # step 2: check database content
        self._check_database_content(user)

        # step 3: check embedding service
        self._check_embedding_service()

        # step 4: test raw embedding retrieval
        self._test_raw_embedding_retrieval(user)

        # step 5: test dimension comparison step by step
        self._test_dimension_comparison(user)

        # step 6: test with fresh embedding
        self._test_fresh_embedding(user)

    def _check_model_structure(self):
        """check the actual model structure"""
        self.stdout.write("🔍 STEP 1: checking model structure...")

        # get model fields
        fields = RAGChunk._meta.get_fields()
        field_info = {}

        for field in fields:
            field_info[field.name] = {
                'type': type(field).__name__,
                'null': getattr(field, 'null', None),
                'blank': getattr(field, 'blank', None)
            }

        self.stdout.write(f"📋 RAGChunk fields:")
        for name, info in field_info.items():
            self.stdout.write(f"   {name}: {info['type']} (null={info['null']}, blank={info['blank']})")

        # check if embedding field exists and what type it is
        if 'embedding' in field_info:
            embedding_field = RAGChunk._meta.get_field('embedding')
            self.stdout.write(f"✅ embedding field found: {type(embedding_field).__name__}")

            # check if it's ArrayField or TextField
            if hasattr(embedding_field, 'base_field'):
                self.stdout.write(f"   base field: {type(embedding_field.base_field).__name__}")
        else:
            self.stdout.write(self.style.ERROR("❌ no 'embedding' field found!"))

        # check if _embedding field exists
        if '_embedding' in field_info:
            self.stdout.write(f"⚠️ '_embedding' field also found - might be causing confusion")

    def _check_database_content(self, user):
        """check what's actually stored in database"""
        self.stdout.write(f"\n🔍 STEP 2: checking database content...")

        chunks = RAGChunk.objects.filter(user=user)
        self.stdout.write(f"📊 found {chunks.count()} chunks for user {user.username}")

        if not chunks.exists():
            self.stdout.write(self.style.WARNING("⚠️ no chunks found - this might be the issue"))
            return

        # examine each chunk's raw data
        for i, chunk in enumerate(chunks):
            self.stdout.write(f"\n📄 chunk {i+1}: {chunk.id}")
            self.stdout.write(f"   type: {chunk.chunk_type}")
            self.stdout.write(f"   content preview: {chunk.content[:100]}...")

            # check raw embedding field value
            try:
                # direct database field access
                raw_embedding = getattr(chunk, 'embedding', None)
                self.stdout.write(f"   raw embedding type: {type(raw_embedding)}")

                if raw_embedding is None:
                    self.stdout.write(self.style.ERROR("   ❌ raw embedding is None"))
                elif isinstance(raw_embedding, str):
                    self.stdout.write(f"   📝 embedding is string, length: {len(raw_embedding)}")
                    # try to parse as json
                    try:
                        parsed = json.loads(raw_embedding)
                        if isinstance(parsed, list):
                            self.stdout.write(f"   ✅ parses to list with {len(parsed)} dimensions")
                        else:
                            self.stdout.write(f"   ❌ parses to {type(parsed)}, not list")
                    except json.JSONDecodeError as e:
                        self.stdout.write(f"   ❌ json parse error: {e}")
                elif isinstance(raw_embedding, list):
                    self.stdout.write(f"   ✅ embedding is list with {len(raw_embedding)} dimensions")
                else:
                    self.stdout.write(f"   ❌ unexpected embedding type: {type(raw_embedding)}")

            except Exception as e:
                self.stdout.write(f"   ❌ error accessing embedding: {e}")

    def _check_embedding_service(self):
        """check embedding service configuration"""
        self.stdout.write(f"\n🔍 STEP 3: checking embedding service...")

        self.stdout.write(f"🔧 embedding service config:")
        self.stdout.write(f"   model: {embedding_service.model}")
        self.stdout.write(f"   dimensions: {embedding_service.dimensions}")
        self.stdout.write(f"   max_tokens: {embedding_service.max_tokens}")

        # test generating a fresh embedding
        try:
            test_result = embedding_service.generate_embedding("test")
            test_embedding = test_result['embedding']
            self.stdout.write(f"✅ test embedding generated:")
            self.stdout.write(f"   dimensions: {len(test_embedding)}")
            self.stdout.write(f"   type: {type(test_embedding)}")
            self.stdout.write(f"   first few values: {test_embedding[:3]}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ failed to generate test embedding: {e}"))

    def _test_raw_embedding_retrieval(self, user):
        """test how embeddings are retrieved from database"""
        self.stdout.write(f"\n🔍 STEP 4: testing raw embedding retrieval...")

        chunks = RAGChunk.objects.filter(user=user)

        for chunk in chunks:
            self.stdout.write(f"\n📄 testing chunk: {chunk.id}")

            # method 1: direct field access
            try:
                direct_embedding = chunk.embedding
                self.stdout.write(f"   direct access type: {type(direct_embedding)}")
                if isinstance(direct_embedding, list):
                    self.stdout.write(f"   direct access dimensions: {len(direct_embedding)}")
                elif isinstance(direct_embedding, str):
                    self.stdout.write(f"   direct access string length: {len(direct_embedding)}")
            except Exception as e:
                self.stdout.write(f"   ❌ direct access error: {e}")

            # method 2: getattr
            try:
                getattr_embedding = getattr(chunk, 'embedding', None)
                self.stdout.write(f"   getattr type: {type(getattr_embedding)}")
                if isinstance(getattr_embedding, list):
                    self.stdout.write(f"   getattr dimensions: {len(getattr_embedding)}")
            except Exception as e:
                self.stdout.write(f"   ❌ getattr error: {e}")

            # method 3: check if there's a property
            if hasattr(RAGChunk, 'embedding') and isinstance(getattr(RAGChunk, 'embedding'), property):
                self.stdout.write(f"   📝 'embedding' is a property")

                # check for _embedding field
                try:
                    private_embedding = getattr(chunk, '_embedding', None)
                    self.stdout.write(f"   _embedding type: {type(private_embedding)}")
                    if isinstance(private_embedding, str):
                        self.stdout.write(f"   _embedding length: {len(private_embedding)}")
                except Exception as e:
                    self.stdout.write(f"   ❌ _embedding access error: {e}")

    def _test_dimension_comparison(self, user):
        """test the exact step where dimension comparison fails"""
        self.stdout.write(f"\n🔍 STEP 5: testing dimension comparison...")

        # generate a fresh query embedding
        try:
            query_result = embedding_service.generate_embedding("test query")
            query_embedding = query_result['embedding']
            query_dims = len(query_embedding)

            self.stdout.write(f"✅ query embedding: {query_dims} dimensions")

            # get stored embeddings and compare dimensions
            chunks = RAGChunk.objects.filter(user=user)

            for chunk in chunks:
                self.stdout.write(f"\n📄 comparing with chunk: {chunk.id}")

                try:
                    chunk_embedding = chunk.embedding

                    if chunk_embedding is None:
                        self.stdout.write(f"   ❌ chunk embedding is None")
                        continue

                    if not isinstance(chunk_embedding, list):
                        self.stdout.write(f"   ❌ chunk embedding is not a list: {type(chunk_embedding)}")
                        continue

                    chunk_dims = len(chunk_embedding)
                    self.stdout.write(f"   chunk dimensions: {chunk_dims}")

                    if chunk_dims == query_dims:
                        self.stdout.write(f"   ✅ dimensions match!")

                        # test actual similarity calculation
                        try:
                            similarity = embedding_service.calculate_similarity(
                                query_embedding, chunk_embedding
                            )
                            self.stdout.write(f"   ✅ similarity calculated: {similarity}")
                        except Exception as e:
                            self.stdout.write(f"   ❌ similarity calculation failed: {e}")
                    else:
                        self.stdout.write(f"   ❌ dimension mismatch: {chunk_dims} vs {query_dims}")

                except Exception as e:
                    self.stdout.write(f"   ❌ error accessing chunk embedding: {e}")

        except Exception as e:
            self.stdout.write(f"❌ failed to generate query embedding: {e}")

    def _test_fresh_embedding(self, user):
        """test creating a completely fresh embedding"""
        self.stdout.write(f"\n🔍 STEP 6: testing fresh embedding creation...")

        # create a test embedding and save it
        test_content = "test content for embedding"

        try:
            # generate embedding
            result = embedding_service.generate_embedding(test_content)
            test_embedding = result['embedding']

            self.stdout.write(f"✅ fresh embedding generated: {len(test_embedding)} dimensions")

            # create a test chunk
            test_chunk = RAGChunk(
                id=f"test_chunk_{user.id}",
                user=user,
                content=test_content,
                chunk_type='profile',
                source='test'
            )

            # try to save the embedding
            test_chunk.embedding = test_embedding
            test_chunk.save()

            self.stdout.write(f"✅ test chunk saved with embedding")

            # retrieve it back
            retrieved_chunk = RAGChunk.objects.get(id=f"test_chunk_{user.id}")
            retrieved_embedding = retrieved_chunk.embedding

            self.stdout.write(f"✅ test chunk retrieved")
            self.stdout.write(f"   retrieved embedding type: {type(retrieved_embedding)}")

            if isinstance(retrieved_embedding, list):
                self.stdout.write(f"   retrieved dimensions: {len(retrieved_embedding)}")

                # test similarity with itself
                try:
                    similarity = embedding_service.calculate_similarity(
                        test_embedding, retrieved_embedding
                    )
                    self.stdout.write(f"   ✅ self-similarity: {similarity} (should be ~1.0)")
                except Exception as e:
                    self.stdout.write(f"   ❌ self-similarity failed: {e}")
            else:
                self.stdout.write(f"   ❌ retrieved embedding is not a list: {type(retrieved_embedding)}")

            # clean up
            retrieved_chunk.delete()
            self.stdout.write(f"✅ test chunk cleaned up")

        except Exception as e:
            self.stdout.write(f"❌ fresh embedding test failed: {e}")

        self.stdout.write(f"\n🎯 DIAGNOSIS COMPLETE!")
        self.stdout.write(f"💡 Look for ❌ errors above to identify the root cause")
