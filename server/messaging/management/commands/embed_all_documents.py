# server/messaging/management/commands/embed_documents.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from documents.models import Document
from messaging.rag_service import rag_service
from core.models import RAGChunk
import time

class Command(BaseCommand):
    help = 'embed documents in rag system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='embed documents for specific user',
        )
        parser.add_argument(
            '--document-id',
            type=int,
            help='embed specific document by id',
        )
        parser.add_argument(
            '--document-type',
            type=str,
            help='embed documents of specific type (transcript, sat_score, etc)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='embed all completed documents',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='re-embed even if document already embedded',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='show what would be embedded without doing it',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Document Embedding ===\n'))

        if options['document_id']:
            self._embed_single_document(options['document_id'], options['force'], options['dry_run'])
        elif options['user_id']:
            self._embed_user_documents(options['user_id'], options['document_type'], options['force'], options['dry_run'])
        elif options['all']:
            self._embed_all_documents(options['document_type'], options['force'], options['dry_run'])
        else:
            self.stdout.write(self.style.ERROR('please specify --document-id, --user-id, or --all'))

    def _embed_single_document(self, document_id, force=False, dry_run=False):
        """embed specific document"""
        try:
            document = Document.objects.get(id=document_id)

            if document.status != 'completed':
                self.stdout.write(
                    self.style.WARNING(
                        f"document {document_id} status is '{document.status}', not 'completed'"
                    )
                )
                return

            self._embed_document(document, force, dry_run)

        except Document.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"document with id {document_id} not found"))

    def _embed_user_documents(self, user_id, document_type=None, force=False, dry_run=False):
        """embed all documents for specific user"""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"user with id {user_id} not found"))
            return

        # get completed documents for user
        documents = Document.objects.filter(user=user, status='completed')

        if document_type:
            documents = documents.filter(document_type=document_type)

        if not documents.exists():
            filter_desc = f" of type '{document_type}'" if document_type else ""
            self.stdout.write(
                self.style.WARNING(f"no completed documents{filter_desc} found for user {user.username}")
            )
            return

        self.stdout.write(f"👤 user: {user.username}")
        self.stdout.write(f"📄 found {documents.count()} completed documents")

        self._embed_document_queryset(documents, force, dry_run)

    def _embed_all_documents(self, document_type=None, force=False, dry_run=False):
        """embed all completed documents"""
        documents = Document.objects.filter(status='completed')

        if document_type:
            documents = documents.filter(document_type=document_type)

        if not documents.exists():
            filter_desc = f" of type '{document_type}'" if document_type else ""
            self.stdout.write(self.style.WARNING(f"no completed documents{filter_desc} found"))
            return

        self.stdout.write(f"📄 found {documents.count()} completed documents")

        if document_type:
            self.stdout.write(f"📋 document type filter: {document_type}")

        self._embed_document_queryset(documents, force, dry_run)

    def _embed_document_queryset(self, documents, force=False, dry_run=False):
        """embed a queryset of documents"""
        if not force:
            # filter out documents that are already embedded
            embedded_doc_ids = RAGChunk.objects.filter(
                chunk_type='document'
            ).values_list('metadata__document_id', flat=True)

            # convert to strings for comparison
            embedded_doc_ids = [str(doc_id) for doc_id in embedded_doc_ids if doc_id]

            documents_to_embed = []
            already_embedded = 0

            for doc in documents:
                if str(doc.id) in embedded_doc_ids:
                    already_embedded += 1
                else:
                    documents_to_embed.append(doc)

            self.stdout.write(f"📊 {already_embedded} documents already embedded")
            self.stdout.write(f"📊 {len(documents_to_embed)} documents need embedding")
        else:
            documents_to_embed = list(documents)
            self.stdout.write(f"🔄 force mode: will re-embed all {len(documents_to_embed)} documents")

        if not documents_to_embed:
            self.stdout.write(self.style.SUCCESS("all documents already embedded!"))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("dry run mode - no actual embedding"))
            for doc in documents_to_embed:
                self.stdout.write(f"would embed: {doc.title} (id: {doc.id}, type: {doc.document_type})")
            return

        # embed documents
        success_count = 0
        error_count = 0
        total_chunks = 0
        start_time = time.time()

        for i, document in enumerate(documents_to_embed, 1):
            self.stdout.write(f"[{i}/{len(documents_to_embed)}] embedding {document.title}...")

            try:
                result = rag_service.embed_document(document.user, document)
                if result['success']:
                    success_count += 1
                    total_chunks += result['chunks_created']

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✅ embedded ({result['chunks_created']} chunks, "
                            f"{result['processing_time']:.2f}s)"
                        )
                    )
                else:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f"  ❌ failed: {result['error']}"))
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"  ❌ exception: {e}"))

        total_time = time.time() - start_time
        self.stdout.write(f"\n📊 summary:")
        self.stdout.write(f"  ✅ successful: {success_count}")
        self.stdout.write(f"  ❌ failed: {error_count}")
        self.stdout.write(f"  📦 total chunks created: {total_chunks}")
        self.stdout.write(f"  ⏱️ total time: {total_time:.2f}s")
        self.stdout.write(f"  ⚡ avg per document: {total_time/max(success_count + error_count, 1):.2f}s")

    def _embed_document(self, document, force=False, dry_run=False):
        """embed single document"""
        self.stdout.write(f"📄 document: {document.title}")
        self.stdout.write(f"   id: {document.id}")
        self.stdout.write(f"   type: {document.document_type}")
        self.stdout.write(f"   user: {document.user.username}")

        # check if document already embedded
        existing_chunks = RAGChunk.objects.filter(
            user=document.user,
            chunk_type='document',
            metadata__document_id=str(document.id)
        )

        if existing_chunks.exists() and not force:
            self.stdout.write(
                self.style.WARNING(
                    f"document already embedded ({existing_chunks.count()} chunks). "
                    f"use --force to re-embed"
                )
            )
            return

        if existing_chunks.exists() and force:
            self.stdout.write(f"force mode: will re-embed (removing {existing_chunks.count()} existing chunks)")

        if dry_run:
            self.stdout.write(self.style.WARNING("dry run mode - would embed document"))
            return

        # embed the document
        try:
            result = rag_service.embed_document(document.user, document)

            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ document embedded successfully\n"
                        f"   chunks created: {result['chunks_created']}\n"
                        f"   processing time: {result['processing_time']:.3f}s\n"
                        f"   document type: {result['document_type']}"
                    )
                )
            else:
                self.stdout.write(self.style.ERROR(f"❌ failed to embed document: {result['error']}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ exception during embedding: {e}"))