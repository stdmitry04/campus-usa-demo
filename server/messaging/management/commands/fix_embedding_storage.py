# server/messaging/management/commands/fix_embeddings.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from core.models import RAGChunk
from core.services.embedding_service import embedding_service
import time

class Command(BaseCommand):
    help = 'fix broken embeddings in existing rag chunks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='fix embeddings for specific user only',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='show what would be fixed without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='regenerate all embeddings, even valid ones',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== FIXING BROKEN EMBEDDINGS ===\n'))

        user_id = options.get('user_id')
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - no changes will be made\n'))

        # get chunks to fix
        chunks_query = RAGChunk.objects.all()
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                chunks_query = chunks_query.filter(user=user)
                self.stdout.write(f"👤 focusing on user: {user.username} (id: {user.id})")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ user {user_id} not found"))
                return

        all_chunks = list(chunks_query)

        if not all_chunks:
            self.stdout.write(self.style.WARNING("⚠️ no chunks found"))
            return

        self.stdout.write(f"📊 found {len(all_chunks)} total chunks")

        # identify broken embeddings
        broken_chunks = []
        valid_chunks = []

        for chunk in all_chunks:
            is_broken = self._is_embedding_broken(chunk)

            if is_broken or force:
                broken_chunks.append(chunk)
            else:
                valid_chunks.append(chunk)

        self.stdout.write(f"❌ broken embeddings: {len(broken_chunks)}")
        self.stdout.write(f"✅ valid embeddings: {len(valid_chunks)}")

        if force:
            self.stdout.write(f"🔄 force mode: will regenerate all embeddings")

        if not broken_chunks:
            self.stdout.write(self.style.SUCCESS("🎉 no broken embeddings found!"))
            return

        # show what will be fixed
        self.stdout.write(f"\n📋 chunks that will be fixed:")
        for i, chunk in enumerate(broken_chunks[:10]):  # show first 10
            reason = self._get_broken_reason(chunk)
            self.stdout.write(f"   [{i+1}] {chunk.id} - {chunk.chunk_type} - {reason}")

        if len(broken_chunks) > 10:
            self.stdout.write(f"   ... and {len(broken_chunks) - 10} more")

        if dry_run:
            self.stdout.write(f"\n🔍 dry run complete - {len(broken_chunks)} chunks need fixing")
            self.stdout.write(f"💡 run without --dry-run to actually fix them")
            return

        # ask for confirmation
        self.stdout.write(f"\n⚠️ this will regenerate embeddings for {len(broken_chunks)} chunks")
        self.stdout.write(f"💰 estimated cost: ~${len(broken_chunks) * 0.0001:.4f} (very rough estimate)")

        confirm = input("\n👉 continue? (y/N): ").lower().strip()
        if confirm != 'y':
            self.stdout.write("❌ cancelled")
            return

        # fix embeddings
        self._fix_embeddings(broken_chunks)

    def _is_embedding_broken(self, chunk):
        """check if a chunk's embedding is broken"""
        try:
            embedding = chunk.embedding

            # check if it's None
            if embedding is None:
                return True

            # check if it's not a list
            if not isinstance(embedding, list):
                return True

            # check if it's empty
            if len(embedding) == 0:
                return True

            # check if it has wrong dimensions (should be 1536)
            if len(embedding) != 1536:
                return True

            # check if it contains non-numeric values
            if not all(isinstance(x, (int, float)) for x in embedding):
                return True

            return False

        except Exception:
            return True

    def _get_broken_reason(self, chunk):
        """get human readable reason why embedding is broken"""
        try:
            embedding = chunk.embedding

            if embedding is None:
                return "embedding is None"
            if not isinstance(embedding, list):
                return f"embedding is {type(embedding).__name__}, not list"
            if len(embedding) == 0:
                return "embedding is empty list"
            if len(embedding) != 1536:
                return f"wrong dimensions: {len(embedding)} (should be 1536)"
            if not all(isinstance(x, (int, float)) for x in embedding):
                return "contains non-numeric values"

            return "unknown issue"

        except Exception as e:
            return f"error accessing embedding: {e}"

    def _fix_embeddings(self, broken_chunks):
        """regenerate embeddings for broken chunks"""
        self.stdout.write(f"\n🔧 fixing {len(broken_chunks)} broken embeddings...")

        start_time = time.time()
        fixed_count = 0
        failed_count = 0

        # process in batches for efficiency
        batch_size = 20
        total_batches = (len(broken_chunks) + batch_size - 1) // batch_size

        for batch_num in range(total_batches):
            batch_start = batch_num * batch_size
            batch_end = min(batch_start + batch_size, len(broken_chunks))
            batch = broken_chunks[batch_start:batch_end]

            self.stdout.write(f"📦 processing batch {batch_num + 1}/{total_batches} ({len(batch)} chunks)")

            # collect texts for batch embedding
            batch_texts = []
            batch_chunks = []

            for chunk in batch:
                if chunk.content and chunk.content.strip():
                    batch_texts.append(chunk.content)
                    batch_chunks.append(chunk)
                else:
                    self.stdout.write(f"   ⚠️ skipping {chunk.id} - empty content")
                    failed_count += 1

            if not batch_texts:
                continue

            try:
                # generate embeddings in batch
                embedding_results = embedding_service.generate_batch_embeddings(batch_texts)

                # update chunks with new embeddings
                with transaction.atomic():
                    for chunk, result in zip(batch_chunks, embedding_results):
                        try:
                            chunk.embedding = result['embedding']
                            chunk.save(update_fields=['embedding'])
                            fixed_count += 1

                            self.stdout.write(f"   ✅ fixed {chunk.id}")

                        except Exception as e:
                            self.stdout.write(f"   ❌ failed to save {chunk.id}: {e}")
                            failed_count += 1

            except Exception as e:
                self.stdout.write(f"   ❌ batch embedding failed: {e}")
                failed_count += len(batch_chunks)

            # add small delay to avoid hitting rate limits
            time.sleep(0.5)

        # summary
        total_time = time.time() - start_time
        self.stdout.write(f"\n🎯 EMBEDDING FIX COMPLETE!")
        self.stdout.write(f"✅ fixed: {fixed_count}")
        self.stdout.write(f"❌ failed: {failed_count}")
        self.stdout.write(f"⏱️ total time: {total_time:.1f}s")

        if fixed_count > 0:
            self.stdout.write(f"\n🧪 testing one fixed chunk...")
            self._test_fixed_chunk(broken_chunks[0] if broken_chunks else None)

    def _test_fixed_chunk(self, chunk):
        """test that a fixed chunk works properly"""
        if not chunk:
            return

        try:
            # reload from database
            chunk.refresh_from_db()

            # check embedding
            embedding = chunk.embedding
            self.stdout.write(f"   📊 chunk {chunk.id}:")
            self.stdout.write(f"      type: {type(embedding)}")
            self.stdout.write(f"      dimensions: {len(embedding) if isinstance(embedding, list) else 'N/A'}")

            if isinstance(embedding, list) and len(embedding) == 1536:
                # test similarity calculation
                test_embedding = embedding_service.generate_embedding("test query")['embedding']
                similarity = embedding_service.calculate_similarity(embedding, test_embedding)
                self.stdout.write(f"      ✅ similarity test passed: {similarity:.3f}")
            else:
                self.stdout.write(f"      ❌ embedding still broken")

        except Exception as e:
            self.stdout.write(f"      ❌ test failed: {e}")