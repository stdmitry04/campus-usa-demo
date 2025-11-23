# server/core/services/validation_service.py
import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from django.conf import settings
from openai import OpenAI
import numpy as np
from dataclasses import dataclass
import re
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
	"""validation result for a document"""
	is_valid: bool
	confidence_score: float
	document_type: str
	identified_fields: Dict[str, Any]
	missing_fields: List[str]
	warnings: List[str]
	embedding: Optional[List[float]] = None


class DocumentReferenceFormats:
	"""defines reference formats for different document types"""

	@staticmethod
	def get_reference_formats() -> Dict[str, Dict]:
		"""return reference document formats for validation"""
		return {
			'transcript': {
				'name': 'high school transcript',
				'required_fields': [
					'school_name', 'student_name', 'grades', 'gpa',
					'graduation_date', 'courses', 'academic_year'
				],
				'optional_fields': [
					'school_address', 'principal_signature', 'counselor_info',
					'class_rank', 'total_students', 'weighted_gpa'
				],
				'content_patterns': [
					r'transcript',
					r'high school',
					r'grade[s]?\s*point\s*average',
					r'gpa',
					r'graduation',
					r'academic\s*year',
					r'course[s]?\s*(title|name)',
					r'semester|quarter',
					r'credit[s]?\s*earned'
				],
				'format_indicators': [
					'official transcript',
					'academic record',
					'student grades',
					'cumulative gpa',
					'course history'
				]
			},

			'sat_score': {
				'name': 'sat score report',
				'required_fields': [
					'student_name', 'test_date', 'total_score',
					'math_score', 'reading_writing_score', 'registration_number'
				],
				'optional_fields': [
					'percentiles', 'test_center', 'high_school_code',
					'essay_scores', 'subscores'
				],
				'content_patterns': [
					r'sat\s*score\s*report',
					r'college\s*board',
					r'total\s*score',
					r'evidence.*based.*reading.*writing',
					r'math\s*score',
					r'test\s*date',
					r'registration\s*number',
					r'percentile'
				],
				'format_indicators': [
					'official sat score report',
					'college board',
					'total score: 400-1600',
					'math section',
					'reading and writing'
				],
				'score_ranges': {
					'total_score': (400, 1600),
					'math_score': (200, 800),
					'reading_writing_score': (200, 800)
				}
			},

			'act_score': {
				'name': 'act score report',
				'required_fields': [
					'student_name', 'test_date', 'composite_score',
					'english_score', 'math_score', 'reading_score', 'science_score'
				],
				'optional_fields': [
					'writing_score', 'stem_score', 'ela_score',
					'test_center', 'high_school_code'
				],
				'content_patterns': [
					r'act\s*score\s*report',
					r'composite\s*score',
					r'english\s*score',
					r'mathematics\s*score',
					r'reading\s*score',
					r'science\s*score',
					r'test\s*date',
					r'student\s*report'
				],
				'format_indicators': [
					'official act score report',
					'composite score',
					'english, math, reading, science',
					'score range: 1-36'
				],
				'score_ranges': {
					'composite_score': (1, 36),
					'english_score': (1, 36),
					'math_score': (1, 36),
					'reading_score': (1, 36),
					'science_score': (1, 36)
				}
			},

			'toefl_score': {
				'name': 'toefl score report',
				'required_fields': [
					'student_name', 'test_date', 'total_score',
					'reading_score', 'listening_score', 'speaking_score', 'writing_score',
					'registration_number'
				],
				'optional_fields': [
					'test_center', 'date_of_birth', 'country_of_citizenship'
				],
				'content_patterns': [
					r'toefl.*ibt.*score\s*report',
					r'test\s*of\s*english.*foreign\s*language',
					r'reading\s*score',
					r'listening\s*score',
					r'speaking\s*score',
					r'writing\s*score',
					r'total\s*score',
					r'educational\s*testing\s*service',
					r'ets'
				],
				'format_indicators': [
					'toefl ibt score report',
					'educational testing service',
					'reading, listening, speaking, writing',
					'total score 0-120'
				],
				'score_ranges': {
					'total_score': (0, 120),
					'reading_score': (0, 30),
					'listening_score': (0, 30),
					'speaking_score': (0, 30),
					'writing_score': (0, 30)
				}
			},

			'ielts_score': {
				'name': 'ielts score report',
				'required_fields': [
					'student_name', 'test_date', 'overall_band_score',
					'listening_score', 'reading_score', 'writing_score', 'speaking_score',
					'candidate_number'
				],
				'optional_fields': [
					'test_center', 'test_report_form_number',
					'date_of_birth', 'nationality'
				],
				'content_patterns': [
					r'ielts.*test\s*report\s*form',
					r'international\s*english\s*language\s*testing\s*system',
					r'overall\s*band\s*score',
					r'listening.*band\s*score',
					r'reading.*band\s*score',
					r'writing.*band\s*score',
					r'speaking.*band\s*score',
					r'candidate\s*number'
				],
				'format_indicators': [
					'ielts test report form',
					'international english language testing system',
					'band scores 0-9',
					'listening, reading, writing, speaking'
				],
				'score_ranges': {
					'overall_band_score': (0, 9),
					'listening_score': (0, 9),
					'reading_score': (0, 9),
					'writing_score': (0, 9),
					'speaking_score': (0, 9)
				}
			},

			'recommendation': {
				'name': 'letter of recommendation',
				'required_fields': [
					'recommender_name', 'recommender_title', 'student_name',
					'recommendation_text', 'signature', 'date'
				],
				'optional_fields': [
					'institution_name', 'contact_information',
					'relationship_duration', 'recommender_qualifications'
				],
				'content_patterns': [
					r'letter.*of.*recommendation',
					r'recommendation.*letter',
					r'reference.*letter',
					r'to\s*whom.*it.*may.*concern',
					r'dear.*admissions.*committee',
					r'recommend.*without.*reservation',
					r'strongly.*recommend',
					r'pleased.*to.*recommend'
				],
				'format_indicators': [
					'formal letter format',
					'letterhead or official header',
					'recommender credentials',
					'specific examples and anecdotes',
					'professional signature'
				]
			},

			# visa-related documents
			'passport': {
				'name': 'passport',
				'required_fields': [
					'passport_number', 'full_name', 'date_of_birth',
					'place_of_birth', 'nationality', 'issue_date', 'expiry_date'
				],
				'optional_fields': [
					'issuing_authority', 'photo', 'signature'
				],
				'content_patterns': [
					r'passport',
					r'passport\s*number',
					r'nationality',
					r'date\s*of\s*birth',
					r'place\s*of\s*birth',
					r'date\s*of\s*issue',
					r'date\s*of\s*expiry'
				],
				'format_indicators': [
					'official government document',
					'passport number format',
					'photo identification',
					'security features'
				]
			},

			'i20': {
				'name': 'form i-20',
				'required_fields': [
					'student_name', 'sevis_id', 'school_name',
					'program_of_study', 'education_level', 'estimated_costs',
					'funding_source', 'dso_signature'
				],
				'optional_fields': [
					'dependents_info', 'employment_authorization',
					'program_end_date'
				],
				'content_patterns': [
					r'form\s*i-20',
					r'certificate.*of.*eligibility',
					r'nonimmigrant.*student.*status',
					r'sevis\s*id',
					r'designated\s*school\s*official',
					r'dso',
					r'student.*exchange.*visitor.*information.*system'
				],
				'format_indicators': [
					'official us government form',
					'sevis id number',
					'school certification',
					'financial information'
				]
			},

			'bank_statement': {
				'name': 'bank statement',
				'required_fields': [
					'account_holder_name', 'account_number', 'bank_name',
					'statement_period', 'account_balance', 'transactions'
				],
				'optional_fields': [
					'bank_address', 'routing_number', 'account_type',
					'average_balance'
				],
				'content_patterns': [
					r'bank\s*statement',
					r'account\s*statement',
					r'account\s*balance',
					r'opening\s*balance',
					r'closing\s*balance',
					r'transaction\s*history',
					r'statement\s*period'
				],
				'format_indicators': [
					'official bank letterhead',
					'account details',
					'transaction records',
					'balance information'
				]
			}
		}


class DocumentValidationService:
	"""validates documents using embeddings and reference formats"""

	def __init__(self):
		self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
		self.reference_formats = DocumentReferenceFormats.get_reference_formats()
		self.embedding_model = "text-embedding-3-small"

	def validate_document(self, document, extracted_text: str) -> ValidationResult:
		"""main validation method for documents"""
		try:
			logger.info(f"validating document: {document.title} (type: {document.document_type})")

			# get reference format for document type
			reference_format = self.reference_formats.get(document.document_type)
			if not reference_format:
				return ValidationResult(
					is_valid=False,
					confidence_score=0.0,
					document_type=document.document_type,
					identified_fields={},
					missing_fields=[],
					warnings=[f"no reference format defined for document type: {document.document_type}"]
				)

			# check if text is too short to be valid
			if len(extracted_text.strip()) < 50:
				return ValidationResult(
					is_valid=False,
					confidence_score=0.0,
					document_type=document.document_type,
					identified_fields={},
					missing_fields=reference_format['required_fields'],
					warnings=["document text too short - may be corrupted or empty"]
				)

			# generate embedding for the document
			document_embedding = self._generate_embedding(extracted_text)

			# validate document format and content
			format_score = self._validate_format_patterns(extracted_text, reference_format)
			field_analysis = self._analyze_document_fields(extracted_text, reference_format)
			content_score = self._validate_content_structure(extracted_text, reference_format)

			# calculate overall confidence score
			confidence_score = (format_score * 0.4 + field_analysis['completeness_score'] * 0.4 + content_score * 0.2)

			# determine if document is valid (threshold can be adjusted)
			is_valid = confidence_score >= 0.7 and len(field_analysis['missing_required_fields']) <= 1

			logger.info(f"validation complete: valid={is_valid}, confidence={confidence_score:.2f}")

			return ValidationResult(
				is_valid=is_valid,
				confidence_score=confidence_score,
				document_type=document.document_type,
				identified_fields=field_analysis['identified_fields'],
				missing_fields=field_analysis['missing_required_fields'],
				warnings=field_analysis['warnings'],
				embedding=document_embedding
			)

		except Exception as e:
			logger.error(f"validation failed for document {document.title}: {e}")
			return ValidationResult(
				is_valid=False,
				confidence_score=0.0,
				document_type=document.document_type,
				identified_fields={},
				missing_fields=[],
				warnings=[f"validation error: {str(e)}"]
			)

	def _generate_embedding(self, text: str) -> Optional[List[float]]:
		"""generate embedding for document text"""
		try:
			# truncate text if too long (embedding model limits)
			max_tokens = 8000  # conservative limit
			if len(text) > max_tokens * 4:  # rough estimate: 4 chars per token
				text = text[:max_tokens * 4]

			response = self.client.embeddings.create(
				model=self.embedding_model,
				input=text
			)

			return response.data[0].embedding

		except Exception as e:
			logger.error(f"failed to generate embedding: {e}")
			return None

	def _validate_format_patterns(self, text: str, reference_format: Dict) -> float:
		"""validate document against format patterns"""
		patterns = reference_format.get('content_patterns', [])
		format_indicators = reference_format.get('format_indicators', [])

		text_lower = text.lower()
		pattern_matches = 0
		indicator_matches = 0

		# check content patterns
		for pattern in patterns:
			if re.search(pattern, text_lower, re.IGNORECASE):
				pattern_matches += 1

		# check format indicators
		for indicator in format_indicators:
			if indicator.lower() in text_lower:
				indicator_matches += 1

		# calculate pattern score
		pattern_score = pattern_matches / max(len(patterns), 1)
		indicator_score = indicator_matches / max(len(format_indicators), 1)

		return (pattern_score + indicator_score) / 2

	def _analyze_document_fields(self, text: str, reference_format: Dict) -> Dict:
		"""analyze document for required and optional fields"""
		required_fields = reference_format.get('required_fields', [])
		optional_fields = reference_format.get('optional_fields', [])

		identified_fields = {}
		missing_required_fields = []
		warnings = []

		text_lower = text.lower()

		# check for required fields
		for field in required_fields:
			field_pattern = self._get_field_pattern(field)
			if re.search(field_pattern, text_lower, re.IGNORECASE):
				# try to extract field value
				extracted_value = self._extract_field_value(text, field, field_pattern)
				identified_fields[field] = extracted_value
			else:
				missing_required_fields.append(field)

		# check for optional fields
		for field in optional_fields:
			field_pattern = self._get_field_pattern(field)
			if re.search(field_pattern, text_lower, re.IGNORECASE):
				extracted_value = self._extract_field_value(text, field, field_pattern)
				identified_fields[field] = extracted_value

		# check score ranges if applicable
		score_ranges = reference_format.get('score_ranges', {})
		for score_field, (min_val, max_val) in score_ranges.items():
			if score_field in identified_fields:
				try:
					score_value = float(identified_fields[score_field])
					if not (min_val <= score_value <= max_val):
						warnings.append(f"{score_field} ({score_value}) outside expected range {min_val}-{max_val}")
				except (ValueError, TypeError):
					warnings.append(f"could not validate {score_field} score format")

		# calculate completeness score
		total_required = len(required_fields)
		found_required = total_required - len(missing_required_fields)
		completeness_score = found_required / max(total_required, 1)

		return {
			'identified_fields': identified_fields,
			'missing_required_fields': missing_required_fields,
			'warnings': warnings,
			'completeness_score': completeness_score
		}

	def _get_field_pattern(self, field_name: str) -> str:
		"""get regex pattern for field extraction"""
		field_patterns = {
			'student_name': r'(student.*name|name.*student|full.*name).*?:?\s*([a-zA-Z\s,]+)',
			'school_name': r'(school.*name|high.*school|institution).*?:?\s*([a-zA-Z\s,]+)',
			'gpa': r'(gpa|grade.*point.*average).*?:?\s*([0-4]\.\d+|\d\.\d+)',
			'total_score': r'(total.*score|composite.*score).*?:?\s*(\d+)',
			'test_date': r'(test.*date|date.*taken|exam.*date).*?:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
			'graduation_date': r'(graduation.*date|graduated).*?:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
			'passport_number': r'(passport.*number|no\.).*?:?\s*([A-Z0-9]+)',
			'sevis_id': r'(sevis.*id|student.*id).*?:?\s*([A-Z]\d+)',
			'account_balance': r'(balance|amount).*?:?\s*\$?(\d+[,\d]*\.?\d*)',
		}

		return field_patterns.get(field_name, f'{field_name.replace("_", ".*")}')

	def _extract_field_value(self, text: str, field_name: str, pattern: str) -> Optional[str]:
		"""extract field value using regex"""
		try:
			match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
			if match and len(match.groups()) >= 2:
				return match.group(2).strip()
			elif match:
				return match.group(0).strip()
			return None
		except Exception:
			return None

	def _validate_content_structure(self, text: str, reference_format: Dict) -> float:
		"""validate overall document structure and content quality"""
		structure_score = 0.0

		# check document length (different types have different expected lengths)
		expected_lengths = {
			'transcript': (500, 5000),
			'sat_score': (200, 2000),
			'act_score': (200, 2000),
			'toefl_score': (200, 1500),
			'ielts_score': (200, 1500),
			'recommendation': (300, 3000),
			'passport': (100, 1000),
			'i20': (300, 2000),
			'bank_statement': (300, 3000)
		}

		doc_type = reference_format.get('name', '').split()[0]
		min_len, max_len = expected_lengths.get(doc_type, (100, 5000))

		text_len = len(text)
		if min_len <= text_len <= max_len:
			structure_score += 0.3
		elif text_len < min_len:
			structure_score += max(0, text_len / min_len * 0.3)
		else:
			structure_score += 0.2  # too long but still valid

		# check for proper formatting indicators
		has_headers = bool(re.search(r'^[A-Z\s]+:|\n[A-Z\s]+:', text, re.MULTILINE))
		has_structured_data = bool(re.search(r'\d+[\.:\-]\s|\|\s|\t', text))
		has_dates = bool(re.search(r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}', text))

		if has_headers:
			structure_score += 0.2
		if has_structured_data:
			structure_score += 0.2
		if has_dates:
			structure_score += 0.3

		return min(structure_score, 1.0)

	def store_validated_embedding(self, document, validation_result: ValidationResult):
		"""store validated document embedding for future ai queries"""
		if validation_result.is_valid and validation_result.embedding:
			try:
				# store embedding in document's extracted_data
				document.extracted_data = {
					**document.extracted_data,
					'validation': {
						'is_valid': validation_result.is_valid,
						'confidence_score': validation_result.confidence_score,
						'identified_fields': validation_result.identified_fields,
						'missing_fields': validation_result.missing_fields,
						'warnings': validation_result.warnings,
						'validated_at': datetime.now().isoformat()
					},
					'embedding': validation_result.embedding,
					'embedding_model': self.embedding_model
				}

				document.save()
				logger.info(f"stored validated embedding for document {document.id}")

			except Exception as e:
				logger.error(f"failed to store embedding for document {document.id}: {e}")

	def get_similar_documents(self, query_embedding: List[float], user_id: int, top_k: int = 5) -> List[Dict]:
		"""find similar validated documents for ai context"""
		try:
			from .models import Document

			# get all validated documents for user
			validated_docs = Document.objects.filter(
				user_id=user_id,
				extracted_data__validation__is_valid=True,
				extracted_data__embedding__isnull=False
			)

			similarities = []

			for doc in validated_docs:
				doc_embedding = doc.extracted_data.get('embedding')
				if doc_embedding:
					# calculate cosine similarity
					similarity = self._cosine_similarity(query_embedding, doc_embedding)
					similarities.append({
						'document_id': str(doc.id),
						'title': doc.title,
						'document_type': doc.document_type,
						'similarity': similarity,
						'identified_fields': doc.extracted_data.get('validation', {}).get('identified_fields', {}),
						'confidence_score': doc.extracted_data.get('validation', {}).get('confidence_score', 0)
					})

			# sort by similarity and return top k
			similarities.sort(key=lambda x: x['similarity'], reverse=True)
			return similarities[:top_k]

		except Exception as e:
			logger.error(f"error finding similar documents: {e}")
			return []

	def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
		"""calculate cosine similarity between two vectors"""
		try:
			vec1_np = np.array(vec1)
			vec2_np = np.array(vec2)

			dot_product = np.dot(vec1_np, vec2_np)
			norm1 = np.linalg.norm(vec1_np)
			norm2 = np.linalg.norm(vec2_np)

			if norm1 == 0 or norm2 == 0:
				return 0.0

			return dot_product / (norm1 * norm2)

		except Exception:
			return 0.0