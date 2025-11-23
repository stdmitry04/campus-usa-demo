# server/messaging/management/commands/rag_stats.py - updated for database storage
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count, Q
from core.models import RAGChunk
from messaging.rag_service import rag_service
from core.services.embedding_service import embedding_service
import json

class Command(BaseCommand):
    help = 'display rag system statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='show detailed stats for specific user',
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='show detailed breakdown per user',
        )
        parser.add_argument(
            '--export',
            type=str,
            help='export stats to json file',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== RAG System Statistics ===\n'))

        if options['user_id']:
            self._display_user_stats(options['user_id'])
        elif options['detailed']:
            self._display_detailed_stats()
        else:
            self._display_system_overview()

        if options['export']:
            self._export_stats(options['export'])

    def _display_system_overview(self):
        """display overall system statistics"""

        # database stats
        total_chunks = RAGChunk.objects.count()
        total_users = RAGChunk.objects.values('user').distinct().count()
        profile_chunks = RAGChunk.objects.filter(chunk_type='profile').count()
        document_chunks = RAGChunk.objects.filter(chunk_type='document').count()

        # document type breakdown
        doc_types = RAGChunk.objects.filter(chunk_type='document').values('source').annotate(
            count=Count('id')
        ).order_by('-count')

        # embedding service stats
        embedding_stats = embedding_service.get_stats()

        self.stdout.write(f"📊 Total Chunks: {total_chunks}")
        self.stdout.write(f"👥 Users with RAG Data: {total_users}")
        self.stdout.write(f"👤 Profile Chunks: {profile_chunks}")
        self.stdout.write(f"📄 Document Chunks: {document_chunks}")

        if doc_types:
            self.stdout.write(f"\n📋 Document Types:")
            for doc_type in doc_types:
                self.stdout.write(f"  - {doc_type['source']}: {doc_type['count']} chunks")

        self.stdout.write(f"\n🔤 Embedding Model: {embedding_stats['model']}")
        self.stdout.write(f"📐 Dimensions: {embedding_stats['dimensions']}")
        self.stdout.write(f"🎯 Max Tokens: {embedding_stats['max_tokens']}")
        self.stdout.write(f"💾 Cache Enabled: {embedding_stats['cache_enabled']}")

        # recent activity
        recent_chunks = RAGChunk.objects.order_by('-created_at')[:5]
        if recent_chunks:
            self.stdout.write(f"\n⏰ Recent Activity:")
            for chunk in recent_chunks:
                self.stdout.write(f"  - {chunk.chunk_type} for user {chunk.user.username} ({chunk.created_at.strftime('%Y-%m-%d %H:%M')})")

    def _display_detailed_stats(self):
        """display detailed per-user statistics"""

        users_with_chunks = User.objects.filter(rag_chunks__isnull=False).distinct()

        if not users_with_chunks:
            self.stdout.write(self.style.WARNING("No users have RAG data yet"))
            return

        self.stdout.write(f"📊 Detailed User Statistics ({users_with_chunks.count()} users):\n")

        for user in users_with_chunks:
            user_stats = rag_service.get_user_stats(user)

            self.stdout.write(f"👤 User: {user.username} (ID: {user.id})")
            self.stdout.write(f"   Total Chunks: {user_stats['total_chunks']}")
            self.stdout.write(f"   Profile: {user_stats['profile_chunks']}")
            self.stdout.write(f"   Documents: {user_stats['document_chunks']}")
            self.stdout.write(f"   Unique Documents: {user_stats['unique_documents']}")

            if user_stats['last_update']:
                self.stdout.write(f"   Last Update: {user_stats['last_update'].strftime('%Y-%m-%d %H:%M:%S')}")

            # show document breakdown for this user
            user_docs = RAGChunk.objects.filter(user=user, chunk_type='document').values('source').annotate(
                count=Count('id')
            )

            if user_docs:
                doc_list = ', '.join([f"{doc['source']}({doc['count']})" for doc in user_docs])
                self.stdout.write(f"   Doc Types: {doc_list}")

            self.stdout.write("")

    def _display_user_stats(self, user_id):
        """display detailed stats for specific user"""

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found"))
            return

        self.stdout.write(f"👤 Detailed Stats for User: {user.username} (ID: {user.id})\n")

        user_chunks = RAGChunk.objects.filter(user=user)

        if not user_chunks.exists():
            self.stdout.write(self.style.WARNING("This user has no RAG data"))
            return

        # overall stats
        user_stats = rag_service.get_user_stats(user)
        self.stdout.write(f"📊 Summary:")
        self.stdout.write(f"   Total Chunks: {user_stats['total_chunks']}")
        self.stdout.write(f"   Profile Chunks: {user_stats['profile_chunks']}")
        self.stdout.write(f"   Document Chunks: {user_stats['document_chunks']}")
        self.stdout.write(f"   Unique Documents: {user_stats['unique_documents']}")

        if user_stats['last_update']:
            self.stdout.write(f"   Last Update: {user_stats['last_update'].strftime('%Y-%m-%d %H:%M:%S')}")

        # profile chunks
        profile_chunks = user_chunks.filter(chunk_type='profile')
        if profile_chunks.exists():
            self.stdout.write(f"\n👤 Profile Chunks:")
            for chunk in profile_chunks:
                content_preview = chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
                self.stdout.write(f"   - {chunk.id}: {content_preview}")
                self.stdout.write(f"     Created: {chunk.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                if chunk.metadata:
                    self.stdout.write(f"     Metadata: {json.dumps(chunk.metadata, indent=6)}")

        # document chunks
        document_chunks = user_chunks.filter(chunk_type='document')
        if document_chunks.exists():
            self.stdout.write(f"\n📄 Document Chunks:")

            # group by document
            docs = {}
            for chunk in document_chunks:
                doc_id = chunk.metadata.get('document_id', 'unknown')
                if doc_id not in docs:
                    docs[doc_id] = []
                docs[doc_id].append(chunk)

            for doc_id, chunks in docs.items():
                doc_title = chunks[0].metadata.get('document_title', 'Unknown Document')
                doc_type = chunks[0].metadata.get('document_type', 'unknown')
                self.stdout.write(f"   📋 Document: {doc_title} (ID: {doc_id}, Type: {doc_type})")
                self.stdout.write(f"      Chunks: {len(chunks)}")

                for chunk in chunks[:3]:  # show first 3 chunks
                    content_preview = chunk.content[:80] + "..." if len(chunk.content) > 80 else chunk.content
                    self.stdout.write(f"      - Chunk {chunk.metadata.get('chunk_index', '?')}: {content_preview}")

                if len(chunks) > 3:
                    self.stdout.write(f"      ... and {len(chunks) - 3} more chunks")

        # test retrieval
        self.stdout.write(f"\n🔍 Test Retrieval:")
        test_queries = ["what are my test scores", "my gpa", "university recommendations"]

        for query in test_queries:
            try:
                result = rag_service.retrieve_context(user, query, top_k=3)
                self.stdout.write(f"   Query: '{query}'")
                self.stdout.write(f"   Found: {len(result['contexts'])} contexts")
                if result['contexts']:
                    best_similarity = max(ctx['similarity'] for ctx in result['contexts'])
                    self.stdout.write(f"   Best similarity: {best_similarity:.3f}")
                self.stdout.write("")
            except Exception as e:
                self.stdout.write(f"   Query: '{query}' - Error: {str(e)}")

    def _export_stats(self, filepath):
        """export statistics to json file"""

        stats = {
            'system_overview': {
                'total_chunks': RAGChunk.objects.count(),
                'total_users': RAGChunk.objects.values('user').distinct().count(),
                'profile_chunks': RAGChunk.objects.filter(chunk_type='profile').count(),
                'document_chunks': RAGChunk.objects.filter(chunk_type='document').count(),
                'embedding_stats': embedding_service.get_stats()
            },
            'user_stats': []
        }

        # add per-user stats
        users_with_chunks = User.objects.filter(rag_chunks__isnull=False).distinct()
        for user in users_with_chunks:
            user_stats = rag_service.get_user_stats(user)
            user_stats['username'] = user.username
            user_stats['user_id'] = user.id
            # convert datetime to string for json serialization
            if user_stats['last_update']:
                user_stats['last_update'] = user_stats['last_update'].isoformat()
            stats['user_stats'].append(user_stats)

        # document type breakdown
        doc_types = RAGChunk.objects.filter(chunk_type='document').values('source').annotate(
            count=Count('id')
        )
        stats['document_types'] = list(doc_types)

        try:
            with open(filepath, 'w') as f:
                json.dump(stats, f, indent=2, default=str)
            self.stdout.write(self.style.SUCCESS(f"📁 Stats exported to {filepath}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to export stats: {e}"))

# example usage:
# python manage.py rag_stats                    # system overview
# python manage.py rag_stats --detailed         # per-user breakdown
# python manage.py rag_stats --user-id 1        # specific user details
# python manage.py rag_stats --export stats.json # export to file