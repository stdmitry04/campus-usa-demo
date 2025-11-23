# core/tasks/validation_tasks.py
from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone
from documents.models import Document
import logging
import re
from typing import Dict
from documents.validators import validate_doc_structure

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def validate_document_task(self, user_id: int, document_id: int):
    """validate document content against declared type after OCR completes"""
    logger.info(f"[TASK] Validation started for document: {document_id}")
    try:
        user = User.objects.get(id=user_id)
        document = Document.objects.get(id=document_id)

        print(f"🔍 [DOCKER] starting validation task for document {document_id}")
        print(f"🔍 [DOCKER] current status: {document.status}")
        logger.info(f"🔍 starting validation for document {document_id}")

        # make sure OCR text is available
        if not document.extracted_text or len(document.extracted_text.strip()) < 10:
            print(f"⚠️ [DOCKER] no OCR text available, retries: {self.request.retries}/{self.max_retries}")
            if self.request.retries < self.max_retries:
                logger.warning(f"no OCR text available for document {document_id}, retrying in 30s...")
                raise self.retry(countdown=30)
            else:
                # give up after max retries
                document.status = 'error'  # Changed from 'validation_error' to 'error'
                document.validation_notes = 'no text content found after OCR processing'
                document.validation_completed_at = timezone.now()
                document.save()
                print(f"❌ [DOCKER] no OCR text after {self.max_retries} retries, set status to 'error'")
                logger.error(f"❌ no OCR text after {self.max_retries} retries for document {document_id}")
                raise Exception('no extracted text available after retries')

        print(f"🔍 [DOCKER] OCR text available: {len(document.extracted_text)} characters")
        print(f"🔍 [DOCKER] declared type: {document.document_type}")

        # run validation function (your existing function with logging)
        validation_result = validate_doc_structure(text=document.extracted_text, declared_type=document.document_type)

        print(f"📊 [DOCKER] validation function returned:")
        print(f"    valid: {validation_result['valid']}")
        print(f"    confidence: {validation_result['confidence']}")
        print(f"    notes: {validation_result.get('validation_notes', '')}")

        # update document with validation results
        document.validation_confidence = validation_result['confidence']
        document.validation_passed = validation_result['valid']
        document.validation_notes = validation_result.get('validation_notes', '')
        document.validation_completed_at = timezone.now()

        # set status based on validation result
        old_status = document.status
        if validation_result['valid']:
            document.status = 'successful'
            print(f"✅ [DOCKER] validation PASSED - setting status: {old_status} → 'successful'")
            logger.info(f"✅ document {document_id} passed validation (confidence: {validation_result['confidence']:.2f})")
        else:
            document.status = 'validation_failed'
            print(f"❌ [DOCKER] validation FAILED - setting status: {old_status} → 'validation_failed'")
            logger.warning(f"❌ document {document_id} failed validation (confidence: {validation_result['confidence']:.2f})")

        # save all changes
        document.save()

        print(f"💾 [DOCKER] document {document_id} saved with:")
        print(f"    status: {document.status}")
        print(f"    validation_passed: {document.validation_passed}")
        print(f"    validation_confidence: {document.validation_confidence}")
        print(f"🔍 [DOCKER] validation task complete")
        logger.info(f"[TASK] Validation finished for document: {document_id}")

        return {
            'document_id': document_id,
            'validation_passed': validation_result['valid'],
            'confidence': validation_result['confidence'],
            'notes': validation_result.get('validation_notes', ''),
            'status': document.status  # Include final status in return
        }

    except Document.DoesNotExist:
        print(f"❌ [DOCKER] document {document_id} not found during validation")
        logger.error(f"document {document_id} not found during validation")
        return {'error': 'document not found'}
    except Exception as e:
        print(f"❌ [DOCKER] validation task exception: {str(e)}")
        logger.error(f"validation failed for document {document_id}: {str(e)}")

        # mark document as having validation error
        try:
            document = Document.objects.get(id=document_id)
            old_status = document.status
            document.status = 'error'  # Changed from 'validation_error' to 'error'
            document.validation_notes = f'validation error: {str(e)}'
            document.validation_completed_at = timezone.now()
            document.save()
            print(f"❌ [DOCKER] exception occurred - setting status: {old_status} → 'error'")
        except Exception as save_error:
            print(f"❌ [DOCKER] failed to save error status: {save_error}")

        if self.request.retries < self.max_retries:
            print(f"🔄 [DOCKER] retrying validation task in 60s (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(countdown=60)

        print(f"❌ [DOCKER] validation task failed after {self.max_retries} retries")
        return {'error': str(e)}