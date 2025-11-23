# server/messaging/management/commands/fix_embeddings.py - fixed for your model structure
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import RAGChunk
from core.services.embedding_service import embedding_service
import json

class Command(BaseCommand):
    help = 'fix embedding dimension mismatches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='only check dimensions without fixing',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='fix embeddings for specific user',
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='fix all embedding dimension issues',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Embedding Dimension Fix ===\n'))

        # get current embedding config
        current_dimensions = embedding_service.dimensions
        current_model = embedding_service.model

        self.stdout.write(f"🔧 current embedding config:")
        self.stdout.write(f"   model: {current_model}")
        self.stdout.write(f"   dimensions: {current_dimensions}")

        if options['user_id']:
            self._fix_user_embeddings(options['user_id'], options['check_only'])
        elif options['fix_all']:
            self._fix_all_embeddings(options['check_only'])
        else:
            self._check_all_dimensions()

    def _check_all_dimensions(self):
        """check dimensions of all stored embeddings"""
        self.stdout.write(f"\n📊 checking all stored embeddings...")

        # use the correct field name - your model has 'embedding' directly
        chunks = RAGChunk.objects.exclude(embedding__isnull=True)

        if not chunks.exists():
            self.stdout.write(self.style.WARNING("no embeddings found in database"))
            return

        dimension_stats = {}
        invalid_embeddings = []

        for chunk in chunks:
            try:
                embedding = chunk.embedding  # direct field access
                if embedding and isinstance(embedding, list):
                    dims = len(embedding)
                    if dims not in dimension_stats:
                        dimension_stats[dims] = []
                    dimension_stats[dims].append(chunk.id)
                else:
                    invalid_embeddings.append(chunk.id)
            except Exception as e:
                self.stdout.write(f"❌ error reading embedding for chunk {chunk.id}: {e}")
                invalid_embeddings.append(chunk.id)

        self.stdout.write(f"📈 dimension analysis:")
        current_dims = embedding_service.dimensions

        for dims, chunk_ids in dimension_stats.items():
            status = "✅" if dims == current_dims else "❌"
            self.stdout.write(f"   {status} {dims} dimensions: {len(chunk_ids)} chunks")

        if invalid_embeddings:
            self.stdout.write(f"   ❌ invalid embeddings: {len(invalid_embeddings)} chunks")

        # show which users are affected
        if any(dims != current_dims for dims in dimension_stats.keys()):
            self.stdout.write(f"\n👥 users with dimension mismatches:")
            wrong_chunks = RAGChunk.objects.filter(
                id__in=[chunk_id for dims, chunk_ids in dimension_stats.items()
                        if dims != current_dims for chunk_id in chunk_ids]
            )
            affected_users = wrong_chunks.values_list('user__username', 'user__id').distinct()
            for username, user_id in affected_users:
                self.stdout.write(f"   - {username} (id: {user_id})")

            self.stdout.write(f"\n🔧 to fix all issues, run:")
            self.stdout.write(f"   python manage.py fix_embeddings --fix-all")

    def _fix_user_embeddings(self, user_id, check_only=False):
        """fix embeddings for specific user"""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"user {user_id} not found"))
            return

        self.stdout.write(f"\n👤 checking user: {user.username} (id: {user_id})")

        chunks = RAGChunk.objects.filter(user=user).exclude(embedding__isnull=True)
        if not chunks.exists():
            self.stdout.write(self.style.WARNING("no embeddings found for this user"))
            return

        current_dims = embedding_service.dimensions
        issues_found = []

        for chunk in chunks:
            try:
                embedding = chunk.embedding
                if embedding and isinstance(embedding, list):
                    dims = len(embedding)
                    if dims != current_dims:
                        issues_found.append((chunk, dims))
                else:
                    issues_found.append((chunk, None))
            except Exception as e:
                self.stdout.write(f"❌ error with chunk {chunk.id}: {e}")
                issues_found.append((chunk, "error"))

        if not issues_found:
            self.stdout.write(self.style.SUCCESS("✅ all embeddings have correct dimensions!"))
            return

        self.stdout.write(f"❌ found {len(issues_found)} chunks with dimension issues:")
        for chunk, dims in issues_found:
            self.stdout.write(f"   - {chunk.id} ({chunk.chunk_type}): {dims} vs {current_dims} expected")

        if check_only:
            self.stdout.write(f"\n🔧 to fix these issues, run:")
            self.stdout.write(f"   python manage.py fix_embeddings --user-id {user_id}")
            return

        # fix the issues
        self.stdout.write(f"\n🔄 re-embedding {len(issues_found)} chunks...")

        # re-embed profile if needed
        profile_issues = [chunk for chunk, dims in issues_found if chunk.chunk_type == 'profile']
        if profile_issues:
            self.stdout.write("🔄 re-embedding profile...")
            from messaging.rag_service import rag_service
            result = rag_service.embed_user_profile(user)
            if result['success']:
                self.stdout.write("   ✅ profile re-embedded successfully")
            else:
                self.stdout.write(f"   ❌ profile re-embedding failed: {result['error']}")

        # re-embed documents if needed
        document_issues = [chunk for chunk, dims in issues_found if chunk.chunk_type == 'document']
        if document_issues:
            # group by document_id
            doc_ids = set(chunk.metadata.get('document_id') for chunk in document_issues
                          if chunk.metadata.get('document_id'))

            self.stdout.write(f"🔄 re-embedding {len(doc_ids)} documents...")

            from documents.models import Document
            from messaging.rag_service import rag_service

            for doc_id in doc_ids:
                try:
                    document = Document.objects.get(id=doc_id, user=user)
                    result = rag_service.embed_document(user, document)
                    if result['success']:
                        self.stdout.write(f"   ✅ document {doc_id} re-embedded")
                    else:
                        self.stdout.write(f"   ❌ document {doc_id} failed: {result['error']}")
                except Document.DoesNotExist:
                    self.stdout.write(f"   ⚠️ document {doc_id} not found, deleting orphaned chunks")
                    RAGChunk.objects.filter(
                        user=user,
                        metadata__document_id=doc_id
                    ).delete()

        self.stdout.write(self.style.SUCCESS(f"✅ completed fixing embeddings for user {user.username}"))

    def _fix_all_embeddings(self, check_only=False):
        """fix all embedding dimension issues"""
        self.stdout.write(f"\n🔧 fixing all embedding dimension issues...")

        if check_only:
            self.stdout.write("📊 check-only mode - no changes will be made")

        current_dims = embedding_service.dimensions
        chunks = RAGChunk.objects.exclude(embedding__isnull=True)

        issues_found = []
        for chunk in chunks:
            try:
                embedding = chunk.embedding
                if embedding and isinstance(embedding, list) and len(embedding) != current_dims:
                    issues_found.append(chunk)
            except:
                issues_found.append(chunk)

        if not issues_found:
            self.stdout.write(self.style.SUCCESS("✅ no dimension issues found!"))
            return

        self.stdout.write(f"❌ found {len(issues_found)} chunks with dimension issues")

        # group by user
        users_affected = {}
        for chunk in issues_found:
            user_id = chunk.user_id
            if user_id not in users_affected:
                users_affected[user_id] = []
            users_affected[user_id].append(chunk)

        self.stdout.write(f"👥 {len(users_affected)} users affected")

        if check_only:
            return

        # fix each user
        for user_id, user_chunks in users_affected.items():
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f"\n🔄 fixing {len(user_chunks)} chunks for {user.username}...")
                self._fix_user_embeddings(user_id, check_only=False)
            except User.DoesNotExist:
                self.stdout.write(f"⚠️ user {user_id} not found, deleting orphaned chunks")
                RAGChunk.objects.filter(user_id=user_id).delete()
