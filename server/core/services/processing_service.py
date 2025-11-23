# server/core/services//processing_service.py
import logging
from typing import Dict
from django.utils import timezone
from core.services.ocr_service import DocumentOCRService
from core.services.validation_service import DocumentValidationService
from celery import shared_task

logger = logging.getLogger(__name__)


class DocumentProcessingService:
	"""coordinates ocr and validation for document processing"""

	def __init__(self):
		self.ocr_service = DocumentOCRService()
		self.validation_service = DocumentValidationService()

	def process_document(self, document) -> Dict[str, any]:
		"""complete document processing pipeline"""
		try:
			logger.info(f"starting processing for document {document.id}: {document.title}")

			# update status to processing
			document.status = 'processing'
			document.save()

			# step 1: extract text using ocr
			ocr_result = self.ocr_service.extract_text_from_document(document)

			if not ocr_result['success']:
				# ocr failed - update document status
				document.status = 'error'
				document.extracted_data = {
					**document.extracted_data,
					'ocr_error': ocr_result['error'],
					'processed_at': timezone.now().isoformat()
				}
				document.save()

				return {
					'success': False,
					'error': f"text extraction failed: {ocr_result['error']}",
					'stage': 'ocr'
				}

			extracted_text = ocr_result['text']
			logger.info(f"extracted {len(extracted_text)} characters from document {document.id}")

			# step 2: validate document using embeddings
			validation_result = self.validation_service.validate_document(document, extracted_text)

			# step 3: store results
			document.extracted_data = {
				**document.extracted_data,
				'ocr_result': {
					'text': extracted_text,
					'metadata': ocr_result['metadata'],
					'char_count': len(extracted_text),
					'extraction_method': ocr_result['metadata'].get('method', 'unknown')
				},
				'validation_result': {
					'is_valid': validation_result.is_valid,
					'confidence_score': validation_result.confidence_score,
					'identified_fields': validation_result.identified_fields,
					'missing_fields': validation_result.missing_fields,
					'warnings': validation_result.warnings
				},
				'processed_at': timezone.now().isoformat()
			}

			# store embedding if document is valid
			if validation_result.is_valid and validation_result.embedding:
				document.extracted_data['embedding'] = validation_result.embedding
				document.extracted_data['embedding_model'] = 'text-embedding-3-small'

			# update document status
			document.status = 'completed'
			document.processed_at = timezone.now()
			document.save()

			logger.info(f"document processing completed for {document.id}: valid={validation_result.is_valid}")

			return {
				'success': True,
				'ocr_result': ocr_result,
				'validation_result': validation_result,
				'extracted_text_length': len(extracted_text),
				'is_valid': validation_result.is_valid,
				'confidence_score': validation_result.confidence_score
			}

		except Exception as e:
			logger.error(f"document processing failed for {document.id}: {e}")

			# update document status to error
			document.status = 'error'
			document.extracted_data = {
				**document.extracted_data,
				'processing_error': str(e),
				'processed_at': timezone.now().isoformat()
			}
			document.save()

			return {
				'success': False,
				'error': str(e),
				'stage': 'processing'
			}


# enhanced ai service integration
class EnhancedAIService:
	"""ai service with document context from validated embeddings"""

	def __init__(self):
		from messaging.ai_service import CollegeApplicationAI
		self.base_ai = CollegeApplicationAI()
		self.validation_service = DocumentValidationService()

	def generate_response_with_documents(self, user_message: str, user_id: int,
	                                     conversation_history=None, user_profile=None) -> Dict:
		"""generate ai response with document context"""
		try:
			# generate query embedding for document similarity search
			query_embedding = self.validation_service._generate_embedding(user_message)

			document_context = ""
			if query_embedding:
				# find similar documents
				similar_docs = self.validation_service.get_similar_documents(
					query_embedding, user_id, top_k=3
				)

				if similar_docs:
					# build document context for ai
					context_parts = ["relevant information from your documents:"]

					for doc in similar_docs:
						if doc['similarity'] > 0.7:  # only include highly relevant docs
							context_parts.append(
								f"- {doc['title']} ({doc['document_type']}): "
								f"{self._format_document_fields(doc['identified_fields'])}"
							)

					if len(context_parts) > 1:
						document_context = "\n".join(context_parts)

			# generate response with document context
			if document_context:
				# add document context to conversation
				enhanced_message = f"{user_message}\n\n{document_context}"
				response = self.base_ai.generate_response(
					enhanced_message, conversation_history, user_profile
				)
				response['used_document_context'] = True
				response['relevant_documents'] = len([d for d in similar_docs if d['similarity'] > 0.7])
			else:
				# no relevant documents found
				response = self.base_ai.generate_response(
					user_message, conversation_history, user_profile
				)
				response['used_document_context'] = False
				response['relevant_documents'] = 0

			return response

		except Exception as e:
			logger.error(f"enhanced ai response failed: {e}")
			# fallback to base ai service
			return self.base_ai.generate_response(user_message, conversation_history, user_profile)

	def _format_document_fields(self, fields: Dict) -> str:
		"""format document fields for ai context"""
		if not fields:
			return "no specific data extracted"

		# format key fields for different document types
		formatted_parts = []

		# academic info
		if 'gpa' in fields:
			formatted_parts.append(f"GPA: {fields['gpa']}")
		if 'total_score' in fields:
			formatted_parts.append(f"Test Score: {fields['total_score']}")
		if 'graduation_date' in fields:
			formatted_parts.append(f"Graduation: {fields['graduation_date']}")

		# financial info
		if 'account_balance' in fields:
			formatted_parts.append(f"Balance: {fields['account_balance']}")

		# personal info
		if 'student_name' in fields:
			formatted_parts.append(f"Name: {fields['student_name']}")
		if 'school_name' in fields:
			formatted_parts.append(f"School: {fields['school_name']}")

		return "; ".join(formatted_parts) if formatted_parts else "basic document info available"