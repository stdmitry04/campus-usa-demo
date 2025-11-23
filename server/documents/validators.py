# server/documents/document_validators.py
from typing import Dict
import re
import os

from django.core.exceptions import ValidationError
from core.validators.document_validators import validate_file_size, validate_file_extension, validate_file_mimetype, validate_filename, \
	sanitize_title
import uuid
from datetime import datetime


def validate_document_file(file):
	"""comprehensive document file validation"""
	print(f"🔍 [DOCKER] validating document file: {file.name}")
	validate_file_size(file)
	validate_file_extension(file)
	validate_file_mimetype(file)
	validate_filename(file)
	print(f"✅ [DOCKER] document file validation passed for: {file.name}")


def validate_document_title(title):
	"""validate and sanitize document title for security"""
	print(f"🔍 [DOCKER] validating document title: '{title}'")

	if not title or not title.strip():
		print(f"❌ [DOCKER] document title validation failed: empty title")
		raise ValidationError('document title is required')

	# sanitize title
	sanitized_title = sanitize_title(title)
	print(f"🧹 [DOCKER] sanitized title: '{title}' -> '{sanitized_title}'")

	if len(sanitized_title) < 1:
		print(f"❌ [DOCKER] document title validation failed: no valid characters after sanitization")
		raise ValidationError('document title must contain valid characters')

	print(f"✅ [DOCKER] document title validation passed: '{sanitized_title}'")
	return sanitized_title


def generate_secure_s3_key(original_filename, user_id=None):
	"""generate secure s3 key for file storage"""
	from core.validators.document_validators import sanitize_title

	print(f"🔑 [DOCKER] generating s3 key for: {original_filename}, user_id: {user_id}")

	# sanitize filename
	clean_filename = _sanitize_filename(original_filename)
	print(f"🧹 [DOCKER] sanitized filename: '{original_filename}' -> '{clean_filename}'")

	# get file extension
	name, ext = os.path.splitext(clean_filename)

	# generate secure path structure
	timestamp = datetime.now()
	unique_id = uuid.uuid4().hex[:8]

	# structure: documents/user_id/year/month/unique_filename.ext
	if user_id:
		s3_key = f"documents/user_{user_id}/{timestamp.year}/{timestamp.month:02d}/{unique_id}_{name[:50]}{ext}"
		print(f"🔑 [DOCKER] generated s3 key: {s3_key}")
	else:
		print(f"❌ [DOCKER] s3 key generation failed: no user_id provided")
		raise ValidationError("user must be authenticated to upload files.")

	return s3_key


def _sanitize_filename(filename):
	"""sanitize filename for s3 storage"""
	print(f"🧹 [DOCKER] sanitizing filename: '{filename}'")

	if not filename:
		print(f"🧹 [DOCKER] empty filename, using 'untitled'")
		return 'untitled'

	# get just the filename without path
	filename = os.path.basename(filename)

	# remove dangerous characters
	dangerous_chars = ['..', '\\', '<', '>', ':', '"', '|', '?', '*', '/', '\x00', '\n', '\r', '\t']
	original_filename = filename
	for char in dangerous_chars:
		filename = filename.replace(char, '_')

	# replace spaces with underscores for s3 compatibility
	filename = filename.replace(' ', '_')

	# remove consecutive underscores
	while '__' in filename:
		filename = filename.replace('__', '_')

	# limit length
	if len(filename) > 100:
		name, ext = os.path.splitext(filename)
		filename = name[:100 - len(ext)] + ext
		print(f"🧹 [DOCKER] filename truncated due to length: {len(original_filename)} chars")

	final_filename = filename or 'untitled'
	print(f"🧹 [DOCKER] filename sanitization complete: '{original_filename}' -> '{final_filename}'")
	return final_filename


def validate_content_type_for_s3(content_type):
	"""validate content type for s3 upload"""
	from django.conf import settings

	print(f"🔍 [DOCKER] validating content type: {content_type}")

	allowed_mimetypes = getattr(settings, 'ALLOWED_DOCUMENT_MIMETYPES', ['application/pdf'])
	print(f"🔍 [DOCKER] allowed mimetypes: {allowed_mimetypes}")

	if content_type not in allowed_mimetypes:
		print(f"❌ [DOCKER] content type validation failed: {content_type} not in allowed types")
		raise ValidationError(
			f'content type "{content_type}" is not allowed for security reasons. '
			f'allowed types: {", ".join(allowed_mimetypes)}'
		)

	print(f"✅ [DOCKER] content type validation passed: {content_type}")
	return content_type


def validate_doc_structure(text="", declared_type="") -> Dict:
	"""validate document content against expected structural patterns for different document types"""

	print(f"\n🔍 [DOCKER] ========== DOCUMENT STRUCTURE VALIDATION ==========")
	print(f"🔍 [DOCKER] declared type: '{declared_type}'")
	print(f"🔍 [DOCKER] text length: {len(text)} characters")
	print(f"🔍 [DOCKER] text preview: '{text[:200]}...'" if len(text) > 200 else f"🔍 [DOCKER] full text: '{text}'")

	# if someone says it's "other", just let it through - no point arguing
	if declared_type == 'other':
		result = {
			'confidence': 1.0,
			'valid': True,
			'matches': ['other_type_specified'],
			'total_patterns': 1,
			'validation_notes': 'other document type - validation bypassed'
		}
		print(f"✅ [DOCKER] document type 'other' - bypassing validation")
		print(f"📊 [DOCKER] final result: {result}")
		print(f"🔍 [DOCKER] ========== VALIDATION COMPLETE ==========\n")
		return result

	# comprehensive patterns for all supported document types
	structure_patterns = {
		'transcript': [
			r'gpa[:\s]+[\d\.]+',
			r'credit[s]?\s*hour[s]?',
			r'\d{4}[-/]\d{4}',  # academic year like 2023-2024
			r'semester|quarter|term',
			r'cumulative\s+gpa',
			r'grade[s]?\s*received',
			r'course\s*(title|name)',
			r'graduation\s*date',
			r'transcript\s*(of|for)',
			r'registrar'
		],

		'sat_score': [
			r'sat\s+score[s]?[:\s]*\d{3,4}',
			r'evidence-based\s+reading',
			r'mathematics[:\s]*\d{3}',
			r'total\s+score[:\s]*\d{4}',
			r'percentile[:\s]*\d{1,2}',
			r'college\s+board',
			r'test\s+date[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
			r'writing\s+(and\s+)?language',
			r'section\s+score[s]?'
		],

		'act_score': [
			r'act\s+composite[:\s]*\d{1,2}',
			r'english[:\s]*\d{1,2}',
			r'mathematics[:\s]*\d{1,2}',
			r'reading[:\s]*\d{1,2}',
			r'science[:\s]*\d{1,2}',
			r'composite\s+score',
			r'test\s+date[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
			r'act\s+inc',
			r'writing\s+score[:\s]*\d{1,2}'
		],

		'toefl_score': [
			r'toefl\s+(ibt|pbt)',
			r'reading[:\s]*\d{1,3}',
			r'listening[:\s]*\d{1,3}',
			r'speaking[:\s]*\d{1,3}',
			r'writing[:\s]*\d{1,3}',
			r'total\s+score[:\s]*\d{2,3}',
			r'institutional\s+code',
			r'ets',
			r'test\s+date[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
		],

		'ielts_score': [
			r'ielts\s+(academic|general)',
			r'overall\s+band\s+score[:\s]*\d\.\d',
			r'listening[:\s]*\d\.\d',
			r'reading[:\s]*\d\.\d',
			r'writing[:\s]*\d\.\d',
			r'speaking[:\s]*\d\.\d',
			r'test\s+report\s+form',
			r'british\s+council|idp',
			r'candidate\s+number'
		],

		'recommendation': [
			r'dear\s+(admissions\s+committee|sir/madam)',
			r'sincerely[,]?\s*\n.*\n.*(professor|dr\.)',
			r'recommend.*without\s+reservation',
			r'it\s+is\s+my\s+pleasure',
			r'academic\s+performance',
			r'to\s+whom\s+it\s+may\s+concern',
			r'i\s+(have\s+)?known\s+.*\s+for',
			r'letter\s+of\s+recommendation',
			r'strongly\s+recommend'
		],

		'personal_statement': [
			r'personal\s+statement',
			r'statement\s+of\s+purpose',
			r'why\s+i\s+(want|choose)',
			r'my\s+(goal|dream|passion)',
			r'i\s+(believe|hope|aspire)',
			r'future\s+(career|plans)',
			r'this\s+experience\s+taught\s+me',
			r'i\s+am\s+(applying|interested)',
			r'throughout\s+my\s+(life|studies)'
		],

		'bank_statement': [
			r'account\s+number[:\s]*[\d\-x]+',
			r'balance[:\s]*\$[\d,]+\.?\d*',
			r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # dates
			r'deposit|withdrawal|transfer',
			r'available\s+balance',
			r'statement\s+period',
			r'beginning\s+balance',
			r'ending\s+balance',
			r'transaction\s+(history|details)'
		],

		'i20': [
			r'sevis\s+id[:\s]*[a-z]?\d+',
			r'program\s+start\s+date',
			r'school\s+code[:\s]*[a-z\d]+',
			r'\$[\d,]+\.?\d*',  # financial amounts
			r'f-?1\s+student',
			r'certificate\s+of\s+eligibility',
			r'dhs',
			r'student\s+and\s+exchange\s+visitor',
			r'program\s+end\s+date'
		],

		'passport': [
			r'passport\s+(no|number)[:\s]*[a-z]?\d+',
			r'nationality[:\s]*[a-z\s]+',
			r'date\s+of\s+birth[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
			r'place\s+of\s+birth',
			r'date\s+of\s+(issue|expiry)',
			r'issuing\s+(authority|country)',
			r'passport',
			r'given\s+name[s]?',
			r'surname'
		],

		'visa': [
			r'visa\s+(type|category)[:\s]*[a-z]\d?',
			r'visa\s+number[:\s]*\d+',
			r'entry\s+(stamp|date)',
			r'valid\s+(until|from)',
			r'multiple\s+entry',
			r'port\s+of\s+entry',
			r'immigration\s+stamp',
			r'admitted\s+(until|for)',
			r'class\s+of\s+admission'
		]
	}

	patterns = structure_patterns.get(declared_type, [])
	print(f"🔍 [DOCKER] found {len(patterns)} patterns for type '{declared_type}'")

	# if we don't have patterns for this type, be cautious but not too strict
	if not patterns:
		result = {
			'confidence': 0.5,
			'valid': True,
			'matches': [],
			'total_patterns': 0,
			'validation_notes': f'no specific patterns defined for {declared_type}'
		}
		print(f"⚠️ [DOCKER] no patterns defined for type '{declared_type}' - using default validation")
		print(f"📊 [DOCKER] final result: {result}")
		print(f"🔍 [DOCKER] ========== VALIDATION COMPLETE ==========\n")
		return result

	# look for pattern matches in the text
	matches = []
	match_details = []

	print(f"🔍 [DOCKER] checking patterns against text...")
	for i, pattern in enumerate(patterns):
		print(f"🔍 [DOCKER] pattern {i+1}/{len(patterns)}: {pattern}")
		search_result = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
		if search_result:
			matches.append(pattern)
			match_details.append({
				'pattern': pattern,
				'matched_text': search_result.group(),
				'position': search_result.span()
			})
			print(f"✅ [DOCKER] MATCH FOUND: '{search_result.group()}' at position {search_result.span()}")
		else:
			print(f"❌ [DOCKER] no match for pattern")

	# calculate confidence based on how many patterns we found
	confidence = len(matches) / len(patterns) if patterns else 0.5
	print(f"📊 [DOCKER] pattern matching results:")
	print(f"📊 [DOCKER] - total patterns: {len(patterns)}")
	print(f"📊 [DOCKER] - matches found: {len(matches)}")
	print(f"📊 [DOCKER] - raw confidence: {confidence:.3f} ({len(matches)}/{len(patterns)})")

	# different thresholds for different document types
	confidence_thresholds = {
		'transcript': 0.4,      # transcripts have lots of variation
		'personal_statement': 0.2,  # very subjective content
		'recommendation': 0.3,   # letters can be quite varied
		'passport': 0.4,        # fairly standardized
		'visa': 0.3,           # varies by country
		'bank_statement': 0.4,  # pretty standardized
		'i20': 0.5,            # very specific format
		'sat_score': 0.4,      # standardized but varies by version
		'act_score': 0.4,      # standardized
		'toefl_score': 0.4,    # standardized
		'ielts_score': 0.4     # standardized
	}

	threshold = confidence_thresholds.get(declared_type, 0.3)
	is_valid = confidence >= threshold

	print(f"📊 [DOCKER] threshold for '{declared_type}': {threshold}")
	print(f"📊 [DOCKER] confidence vs threshold: {confidence:.3f} {'≥' if is_valid else '<'} {threshold}")
	print(f"📊 [DOCKER] validation result: {'PASS' if is_valid else 'FAIL'}")

	# additional validation notes based on what we found
	validation_notes = []
	if confidence < threshold:
		validation_notes.append(f'low confidence: {confidence:.2f} < {threshold}')
		print(f"⚠️ [DOCKER] low confidence warning added")
	if len(matches) == 0:
		validation_notes.append('no characteristic patterns found')
		print(f"⚠️ [DOCKER] no patterns found warning added")
	elif len(matches) == len(patterns):
		validation_notes.append('all expected patterns found')
		print(f"✅ [DOCKER] all patterns found note added")

	result = {
		'confidence': round(confidence, 3),
		'valid': is_valid,
		'matches': matches,
		'total_patterns': len(patterns),
		'match_details': match_details,
		'threshold_used': threshold,
		'validation_notes': '; '.join(validation_notes) if validation_notes else 'validation passed'
	}

	print(f"📊 [DOCKER] final validation result:")
	print(f"📊 [DOCKER] - confidence: {result['confidence']}")
	print(f"📊 [DOCKER] - valid: {result['valid']}")
	print(f"📊 [DOCKER] - matches: {len(result['matches'])}/{result['total_patterns']}")
	print(f"📊 [DOCKER] - threshold: {result['threshold_used']}")
	print(f"📊 [DOCKER] - notes: {result['validation_notes']}")
	print(f"🔍 [DOCKER] ========== VALIDATION COMPLETE ==========\n")

	return result