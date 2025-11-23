# server/messaging/management/commands/debug_rag.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from messaging.rag_service import rag_service
from messaging.ai_service import ai_service
from core.models import RAGChunk
import json

class Command(BaseCommand):
    help = 'debug rag system step by step'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            required=True,
            help='user id to debug',
        )
        parser.add_argument(
            '--query',
            type=str,
            default='tell me about myself',
            help='query to test with',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== RAG Debug Session ===\n'))

        user_id = options['user_id']
        query = options['query']

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"user {user_id} not found"))
            return

        self.stdout.write(f"👤 user: {user.username} (id: {user.id})")
        self.stdout.write(f"❓ query: '{query}'\n")

        # step 1: check if user has any rag data
        self._check_user_data(user)

        # step 2: test context retrieval
        self._test_context_retrieval(user, query)

        # step 3: test prompt building
        self._test_prompt_building(user, query)

        # step 4: test full ai response
        self._test_ai_response(user, query)

    def _check_user_data(self, user):
        """check what rag data exists for user"""
        self.stdout.write("📊 checking user rag data...")

        chunks = RAGChunk.objects.filter(user=user)

        if not chunks.exists():
            self.stdout.write(self.style.ERROR("❌ no rag chunks found for this user!"))
            self.stdout.write("   try running: python manage.py embed_profiles --user-id {} --force".format(user.id))
            return False

        profile_chunks = chunks.filter(chunk_type='profile')
        document_chunks = chunks.filter(chunk_type='document')

        self.stdout.write(f"✅ found {chunks.count()} total chunks:")
        self.stdout.write(f"   👤 profile chunks: {profile_chunks.count()}")
        self.stdout.write(f"   📄 document chunks: {document_chunks.count()}")

        # show profile content
        if profile_chunks.exists():
            profile = profile_chunks.first()
            self.stdout.write(f"\n👤 profile content preview:")
            self.stdout.write(f"   {profile.content[:200]}...")

        # show document content
        if document_chunks.exists():
            self.stdout.write(f"\n📄 document chunks preview:")
            for chunk in document_chunks[:3]:
                doc_title = chunk.metadata.get('document_title', 'Unknown')
                self.stdout.write(f"   - {doc_title}: {chunk.content[:100]}...")

        return True

    def _test_context_retrieval(self, user, query):
        """test context retrieval with detailed output"""
        self.stdout.write(f"\n🔍 testing context retrieval for: '{query}'")

        try:
            result = rag_service.retrieve_context(user, query, top_k=5)

            self.stdout.write(f"   processing time: {result['processing_time']:.3f}s")
            self.stdout.write(f"   has context: {result['has_context']}")
            self.stdout.write(f"   contexts found: {len(result['contexts'])}")

            if not result['has_context']:
                self.stdout.write(self.style.WARNING("⚠️ no relevant context found!"))

                # try different queries to see if any work
                test_queries = [
                    "gpa", "test scores", "sat", "transcript", "university",
                    "student", "academic", "school", "grades"
                ]

                self.stdout.write("🔄 trying different query terms...")
                for test_query in test_queries:
                    test_result = rag_service.retrieve_context(user, test_query, top_k=3)
                    if test_result['has_context']:
                        best_similarity = max(ctx['similarity'] for ctx in test_result['contexts'])
                        self.stdout.write(f"   ✅ '{test_query}' found {len(test_result['contexts'])} contexts (best: {best_similarity:.3f})")
                        break
                else:
                    self.stdout.write(self.style.ERROR("   ❌ no queries returned relevant context"))
                return

            # show context details
            self.stdout.write(f"\n📋 context details:")
            for i, ctx in enumerate(result['contexts'], 1):
                embedding_dim = len(RAGChunk.objects.get(
                    user=user,
                    chunk_type=ctx['type'],
                    content=ctx['content']
                ).embedding)

                self.stdout.write(f"       embedding dim: {embedding_dim}")

                self.stdout.write(f"   [{i}] type: {ctx['type']}, similarity: {ctx['similarity']:.3f}")
                self.stdout.write(f"       source: {ctx['source']}")
                self.stdout.write(f"       content: {ctx['content'][:150]}...")
                self.stdout.write("")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ context retrieval failed: {e}"))

    def _test_prompt_building(self, user, query):
        """test contextual prompt building"""
        self.stdout.write(f"\n🛠️ testing prompt building...")

        try:
            prompt_result = rag_service.build_contextual_prompt(user, query, max_context_length=3000)

            self.stdout.write(f"   has context: {prompt_result['has_context']}")
            self.stdout.write(f"   contexts used: {len(prompt_result['contexts_used'])}")
            self.stdout.write(f"   context length: {prompt_result.get('context_length', 0)} chars")

            if prompt_result['has_context']:
                self.stdout.write(f"\n📝 system prompt (first 500 chars):")
                self.stdout.write(f"   {prompt_result['system_prompt'][:500]}...")

                self.stdout.write(f"\n📝 user prompt:")
                self.stdout.write(f"   {prompt_result['user_prompt']}")

                # this is the key - show exactly what would be sent to gpt
                self.stdout.write(f"\n🤖 FULL PROMPT THAT WILL BE SENT TO GPT:")
                self.stdout.write(self.style.SUCCESS("=" * 60))
                self.stdout.write(f"SYSTEM: {prompt_result['system_prompt']}")
                self.stdout.write(f"USER: {prompt_result['user_prompt']}")
                self.stdout.write(self.style.SUCCESS("=" * 60))
            else:
                self.stdout.write(self.style.WARNING("⚠️ no context available for prompt"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ prompt building failed: {e}"))

    def _test_ai_response(self, user, query):
        """test full ai response generation"""
        self.stdout.write(f"\n🤖 testing ai response generation...")

        try:
            # force rag usage
            result = ai_service.generate_response(
                user_message=query,
                user=user,
                use_rag=True
            )

            self.stdout.write(f"   success: {result['success']}")
            self.stdout.write(f"   rag used: {result['rag_used']}")
            self.stdout.write(f"   model: {result['model_used']}")
            self.stdout.write(f"   response time: {result['response_time']:.3f}s")

            if result['success']:
                self.stdout.write(f"\n💬 ai response:")
                self.stdout.write(self.style.SUCCESS("-" * 60))
                self.stdout.write(result['content'])
                self.stdout.write(self.style.SUCCESS("-" * 60))

                # show rag stats
                if 'rag_stats' in result:
                    rag_stats = result['rag_stats']
                    self.stdout.write(f"\n📊 rag usage stats:")
                    self.stdout.write(f"   contexts used: {rag_stats.get('contexts_used', 0)}")
                    self.stdout.write(f"   context types: {rag_stats.get('context_types', [])}")
                    self.stdout.write(f"   has context: {rag_stats.get('has_context', False)}")

                    if not rag_stats.get('has_context', False):
                        self.stdout.write(self.style.ERROR("❌ rag stats show no context was used!"))

            else:
                self.stdout.write(self.style.ERROR(f"❌ ai response failed: {result.get('error')}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ ai response generation failed: {e}"))