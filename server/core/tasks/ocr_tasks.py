# server/documents/tasks/ocr_tasks.py - celery tasks for async document ocr processing
from celery import shared_task
from django.contrib.auth.models import User
from django.apps import apps
from core.services.ocr_service import DocumentOCRService
from core.tasks.embedding_tasks import embed_document_task
from celery_app import app
import logging

logger = logging.getLogger(__name__)

ocr_service = DocumentOCRService()


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document_ocr_task(self, user_id: int, document_id: int):
    """async task to extract text from document using ocr"""
    logger.info(f"[TASK] OCR started for document: {document_id}")
    try:
        user = User.objects.get(id=user_id)

        # get document model dynamically to avoid circular imports
        Document = apps.get_model('documents', 'Document')
        document = Document.objects.get(id=document_id, user=user)

        logger.info(f"🔄 starting ocr processing for user {user_id}, document {document_id} ({document.title})")

        # run ocr extraction
        ocr_result = ocr_service.extract_text_from_document(document)

        if ocr_result['success']:
            # save extracted text to document
            document.extracted_text = ocr_result['text']
            document.ocr_metadata = ocr_result.get('metadata', {})
            document.ocr_status = 'completed'
            document.save(update_fields=['extracted_text', 'ocr_metadata', 'ocr_status'])

            logger.info(f"[TASK] OCR finished for document: {document_id}")


            return {
                'success': True,
                'user_id': user_id,
                'document_id': document_id,
                'text_length': len(ocr_result['text']),
                'metadata': ocr_result.get('metadata', {})
            }
        else:
            # mark document as failed
            document.ocr_status = 'failed'
            document.ocr_error = ocr_result.get('error', 'unknown error')
            document.save(update_fields=['ocr_status', 'ocr_error'])

            logger.error(f"❌ ocr failed for document {document_id}: {ocr_result.get('error')}")
            raise Exception(f"ocr extraction failed: {ocr_result.get('error')}")

    except User.DoesNotExist:
        logger.error(f"❌ user {user_id} not found for ocr processing")
        return {'success': False, 'error': 'user not found'}

    except Exception as exc:
        logger.error(f"❌ ocr task failed for user {user_id}, document {document_id}: {exc}")

        # mark document as failed if we can access it
        try:
            Document = apps.get_model('documents', 'Document')
            document = Document.objects.get(id=document_id, user_id=user_id)
            document.ocr_status = 'failed'
            document.ocr_error = str(exc)
            document.save(update_fields=['ocr_status', 'ocr_error'])
        except:
            pass  # document might not exist or other issues

        # retry on certain errors
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 retrying ocr for document {document_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

        return {'success': False, 'error': str(exc)}


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def batch_process_ocr_task(self, user_id: int, document_ids: list = None, trigger_embedding: bool = True):
    """async task to process ocr for multiple documents"""
    try:
        user = User.objects.get(id=user_id)

        # get documents to process
        Document = apps.get_model('documents', 'Document')
        if document_ids:
            documents = Document.objects.filter(id__in=document_ids, user=user)
        else:
            # process all documents that need ocr
            documents = Document.objects.filter(
                user=user,
                ocr_status__in=['pending', 'failed', None]
            )

        logger.info(f"🔄 starting batch ocr processing for user {user_id} ({documents.count()} documents)")

        results = []
        success_count = 0
        failed_count = 0

        for document in documents:
            try:
                # mark as processing
                document.ocr_status = 'processing'
                document.save(update_fields=['ocr_status'])

                # run ocr
                ocr_result = ocr_service.extract_text_from_document(document)

                if ocr_result['success']:
                    # save extracted text
                    document.extracted_text = ocr_result['text']
                    document.ocr_metadata = ocr_result.get('metadata', {})
                    document.ocr_status = 'completed'
                    document.save(update_fields=['extracted_text', 'ocr_metadata', 'ocr_status'])

                    # schedule embedding if requested
                    embedding_task_id = None
                    if trigger_embedding:
                        try:
                            embedding_task = embed_document_task.delay(user_id, document.id)
                            embedding_task_id = embedding_task.id
                        except Exception as e:
                            logger.warning(f"⚠️ failed to schedule embedding for document {document.id}: {e}")

                    results.append({
                        'document_id': document.id,
                        'success': True,
                        'text_length': len(ocr_result['text']),
                        'embedding_task_id': embedding_task_id
                    })
                    success_count += 1

                else:
                    # mark as failed
                    document.ocr_status = 'failed'
                    document.ocr_error = ocr_result.get('error', 'unknown error')
                    document.save(update_fields=['ocr_status', 'ocr_error'])

                    results.append({
                        'document_id': document.id,
                        'success': False,
                        'error': ocr_result.get('error')
                    })
                    failed_count += 1

            except Exception as e:
                logger.error(f"❌ failed to process ocr for document {document.id}: {e}")

                # mark as failed
                try:
                    document.ocr_status = 'failed'
                    document.ocr_error = str(e)
                    document.save(update_fields=['ocr_status', 'ocr_error'])
                except:
                    pass

                results.append({
                    'document_id': document.id,
                    'success': False,
                    'error': str(e)
                })
                failed_count += 1

        logger.info(f"✅ batch ocr completed for user {user_id}: {success_count} success, {failed_count} failed")

        return {
            'success': True,
            'user_id': user_id,
            'total_documents': len(results),
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        }

    except User.DoesNotExist:
        logger.error(f"❌ user {user_id} not found for batch ocr")
        return {'success': False, 'error': 'user not found'}

    except Exception as exc:
        logger.error(f"❌ batch ocr task failed for user {user_id}: {exc}")

        # retry with exponential backoff
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 retrying batch ocr for user {user_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=120 * (2 ** self.request.retries))

        return {'success': False, 'error': str(exc)}


@shared_task
def reprocess_failed_documents_task(user_id: int = None):
    """reprocess documents that failed ocr extraction"""
    try:
        Document = apps.get_model('documents', 'Document')

        # get failed documents
        failed_docs = Document.objects.filter(ocr_status='failed')
        if user_id:
            failed_docs = failed_docs.filter(user_id=user_id)

        if not failed_docs.exists():
            logger.info("🔍 no failed documents found to reprocess")
            return {'success': True, 'message': 'no failed documents found'}

        logger.info(f"🔄 reprocessing {failed_docs.count()} failed documents")

        # group by user and trigger batch processing
        user_doc_map = {}
        for doc in failed_docs:
            if doc.user_id not in user_doc_map:
                user_doc_map[doc.user_id] = []
            user_doc_map[doc.user_id].append(doc.id)

        task_ids = []
        for uid, doc_ids in user_doc_map.items():
            task = batch_process_ocr_task.delay(uid, doc_ids)
            task_ids.append(task.id)

        return {
            'success': True,
            'users_processed': len(user_doc_map),
            'total_documents': failed_docs.count(),
            'task_ids': task_ids
        }

    except Exception as e:
        logger.error(f"❌ failed to reprocess failed documents: {e}")
        return {'success': False, 'error': str(e)}


# convenience functions for triggering tasks
def trigger_document_ocr(user_id: int, document_id: int, trigger_embedding: bool = True, async_mode: bool = True):
    """trigger ocr processing for a single document"""
    if async_mode:
        return process_document_ocr_task.delay(user_id, document_id, trigger_embedding)
    else:
        return process_document_ocr_task(user_id, document_id, trigger_embedding)


def trigger_batch_ocr(user_id: int, document_ids: list = None, trigger_embedding: bool = True, async_mode: bool = True):
    """trigger batch ocr processing"""
    if async_mode:
        return batch_process_ocr_task.delay(user_id, document_ids, trigger_embedding)
    else:
        return batch_process_ocr_task(user_id, document_ids, trigger_embedding)


def trigger_failed_reprocessing(user_id: int = None):
    """trigger reprocessing of failed documents"""
    return reprocess_failed_documents_task.delay(user_id)