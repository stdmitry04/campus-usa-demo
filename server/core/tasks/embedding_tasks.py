# server/core/tasks/embedding_tasks.py - UPDATED WITH CHUNKING SUPPORT
from celery import shared_task
from django.contrib.auth.models import User
from django.apps import apps
from core.services.embedding_service import get_embedding_service, ProfileChunker
import logging
import time
import traceback

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def embed_user_profile_task(self, user_id: int):
    """async task to embed and store user profile as chunks in qdrant"""
    start_time = time.time()

    logger.info(f"profile chunked embedding start: user_id={user_id}")

    try:
        # get user
        logger.info(f"fetching user {user_id}...")
        user = User.objects.get(id=user_id)
        logger.info(f"user found: {user.username}")

        # get embedding service
        logger.info(f"getting embedding service...")
        embedding_service = get_embedding_service()

        if not embedding_service:
            logger.error(f"embedding service not available")
            raise Exception("embedding service not available")

        logger.info(f"embedding service available")

        # check qdrant connection
        if not embedding_service.qdrant_client:
            logger.error(f"qdrant client not connected")
            raise Exception("qdrant client not connected")

        logger.info(f"qdrant client connected")

        # extract profile data from user using existing extraction function
        logger.info(f"extracting profile data...")
        profile_text, profile_data = _extract_user_profile(user)

        # also extract user data separately for chunking
        user_data = {
            'username': user.username,
            'email': user.email or '',
            'first_name': user.first_name or '',
            'last_name': user.last_name or ''
        }

        logger.info(f"profile data extracted:")
        logger.info(f"   user_data keys: {list(user_data.keys())}")
        logger.info(f"   profile_data keys: {list(profile_data.keys())}")
        logger.info(f"   original text length: {len(profile_text)}")

        # use new chunked embedding method
        logger.info(f"storing chunked profile embeddings in qdrant...")
        chunk_ids = embedding_service.store_chunked_profile_embeddings(
            user_id=user_id,
            user_data=user_data,
            profile_data=profile_data
        )

        processing_time = time.time() - start_time

        if chunk_ids:
            logger.info(f"profile chunked embedding success: user {user_id} ({len(chunk_ids)} chunks, {processing_time:.2f}s)")
            logger.info(f"chunks created: {list(chunk_ids.keys())}")

            # verify storage
            logger.info(f"verifying storage...")
            user_data_check = embedding_service.get_user_data(user_id)
            chunks_found = len(user_data_check['profile_chunks'])
            logger.info(f"verification: found {chunks_found} chunks in qdrant")

            return {
                'success': True,
                'user_id': user_id,
                'processing_time': processing_time,
                'chunks_created': list(chunk_ids.keys()),
                'total_chunks': len(chunk_ids),
                'chunk_ids': chunk_ids,
                'profile_data': profile_data
            }
        else:
            logger.error(f"profile chunked embedding failed: no chunks created")
            raise Exception("failed to create profile chunks")

    except User.DoesNotExist:
        logger.error(f"profile embedding failed: user {user_id} not found")
        return {'success': False, 'error': 'user not found', 'user_id': user_id}

    except Exception as exc:
        logger.error(f"profile embedding failed: user {user_id}: {exc}")
        logger.error(f"full traceback: {traceback.format_exc()}")

        # retry on certain errors
        if self.request.retries < self.max_retries:
            logger.info(f"retrying profile embedding for user {user_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

        return {
            'success': False,
            'error': str(exc),
            'user_id': user_id,
            'processing_time': time.time() - start_time
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def update_profile_chunks_task(self, user_id: int, chunk_types: list):
    """async task to update specific profile chunks"""
    start_time = time.time()

    logger.info(f"profile chunk update start: user_id={user_id}, chunks={chunk_types}")

    try:
        # get user
        user = User.objects.get(id=user_id)
        logger.info(f"user found: {user.username}")

        # get embedding service
        embedding_service = get_embedding_service()
        if not embedding_service or not embedding_service.qdrant_client:
            raise Exception("embedding service not available")

        # extract current profile data
        logger.info(f"extracting current profile data...")
        profile_text, profile_data = _extract_user_profile(user)

        user_data = {
            'username': user.username,
            'email': user.email or '',
            'first_name': user.first_name or '',
            'last_name': user.last_name or ''
        }

        # update specific chunks
        logger.info(f"updating profile chunks: {chunk_types}")
        chunk_ids = embedding_service.update_specific_profile_chunks(
            user_id=user_id,
            user_data=user_data,
            profile_data=profile_data,
            chunk_types=chunk_types
        )

        processing_time = time.time() - start_time

        if chunk_ids:
            logger.info(f"profile chunks updated successfully: user {user_id} ({len(chunk_ids)} chunks, {processing_time:.2f}s)")
            return {
                'success': True,
                'user_id': user_id,
                'chunks_updated': list(chunk_ids.keys()),
                'processing_time': processing_time,
                'chunk_ids': chunk_ids
            }
        else:
            logger.warning(f"no chunks updated for user {user_id}")
            return {
                'success': True,
                'user_id': user_id,
                'chunks_updated': [],
                'processing_time': processing_time,
                'message': 'no chunks needed updating'
            }

    except Exception as exc:
        logger.error(f"profile chunk update failed: user {user_id}: {exc}")

        if self.request.retries < self.max_retries:
            logger.info(f"retrying profile chunk update for user {user_id}")
            raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))

        return {
            'success': False,
            'error': str(exc),
            'user_id': user_id,
            'processing_time': time.time() - start_time
        }


# convenience tasks for different types of updates
@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def update_basic_info_chunks_task(self, user_id: int):
    """update chunks affected by basic info changes (name, email, phone)"""
    return update_profile_chunks_task(user_id, ['basic_personal', 'profile_summary'])


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def update_academic_chunks_task(self, user_id: int):
    """update chunks affected by academic info changes"""
    return update_profile_chunks_task(user_id, [
        'high_school', 'test_scores', 'profile_summary',
        'score_narrative', 'academic_standing', 'university_match'
    ])


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def update_preferences_chunks_task(self, user_id: int):
    """update chunks affected by preference changes"""
    return update_profile_chunks_task(user_id, [
        'application_prefs', 'profile_summary', 'university_match'
    ])


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def embed_document_task(self, user_id: int, document_id: int):
    """async task to embed and store document in qdrant"""
    logger.info(f"[TASK] Embedding started for document: {document_id}")
    start_time = time.time()

    try:
        # get user
        logger.info(f"fetching user {user_id}...")
        user = User.objects.get(id=user_id)
        logger.info(f"user found: {user.username}")

        # get embedding service
        logger.info(f"getting embedding service...")
        embedding_service = get_embedding_service()

        if not embedding_service:
            logger.error(f"embedding service not available")
            raise Exception("embedding service not available")

        logger.info(f"embedding service available")

        # dynamically get the document model to avoid circular imports
        logger.info(f"fetching document {document_id}...")
        Document = apps.get_model('documents', 'Document')
        document = Document.objects.get(id=document_id, user=user)
        logger.info(f"document found: {document.title}")

        # extract and chunk document content
        logger.info(f"extracting and chunking document content...")
        document_chunks, document_type = _extract_and_chunk_document(document)

        logger.info(f"document processing results:")
        logger.info(f"   document_type: {document_type}")
        logger.info(f"   chunks created: {len(document_chunks)}")

        if document_chunks:
            for i, chunk in enumerate(document_chunks[:3]):  # log first 3 chunks
                logger.info(f"   chunk {i}: {len(chunk)} chars - {chunk[:100]}...")

        if not document_chunks:
            logger.warning(f"no content extracted from document {document_id}")
            return {
                'success': False,
                'error': 'no document content',
                'user_id': user_id,
                'document_id': document_id,
                'processing_time': time.time() - start_time
            }

        # store document embeddings in qdrant
        logger.info(f"storing document embeddings in qdrant...")
        point_ids = embedding_service.store_document_embeddings(
            user_id=user_id,
            document_texts=document_chunks,
            source=document_type,
            document_id=str(document_id)  # pass document ID
        )

        processing_time = time.time() - start_time
        chunks_created = len(point_ids)

        logger.info(f"embedding storage results:")
        logger.info(f"   point_ids returned: {len(point_ids)}")
        logger.info(f"   point_ids: {point_ids[:5]}...")  # first 5 ids

        if point_ids:
            logger.info(f"document embedding success: user {user_id}, document {document_id} ({chunks_created} chunks, {processing_time:.2f}s)")

            # verify storage
            logger.info(f"verifying storage...")
            user_data = embedding_service.get_user_data(user_id)
            doc_chunks_found = [
                doc for doc in user_data['documents']
                if doc['data'].get('document_id') == str(document_id)
            ]
            logger.info(f"verification: found {len(doc_chunks_found)} chunks in qdrant")

            # document.status = 'successful'
            document.save()
            logger.info(f"[TASK] Embedding finished for document: {document_id}")
            return {
                'success': True,
                'user_id': user_id,
                'document_id': document_id,
                'chunks_created': chunks_created,
                'processing_time': processing_time,
                'document_type': document_type,
                'point_ids': point_ids
            }
        else:
            logger.error(f"document embedding failed: store_document_embeddings returned empty list")
            raise Exception("failed to store document embeddings")

    except User.DoesNotExist:
        logger.error(f"document embedding failed: user {user_id} not found")
        return {'success': False, 'error': 'user not found', 'user_id': user_id}

    except Exception as exc:
        logger.error(f"document embedding failed: user {user_id}, document {document_id}: {exc}")
        logger.error(f"full traceback: {traceback.format_exc()}")

        # retry on certain errors
        if self.request.retries < self.max_retries:
            logger.info(f"retrying document embedding for user {user_id}, document {document_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

        return {
            'success': False,
            'error': str(exc),
            'user_id': user_id,
            'document_id': document_id,
            'processing_time': time.time() - start_time
        }


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def embed_multiple_documents_task(self, user_id: int, document_ids: list):
    """async task to embed multiple documents for a user - UNCHANGED"""
    start_time = time.time()
    results = []

    logger.info(f"batch embedding start: user_id={user_id}, documents={len(document_ids)}")

    try:
        user = User.objects.get(id=user_id)
        embedding_service = get_embedding_service()

        if not embedding_service:
            raise Exception("embedding service not available")

        Document = apps.get_model('documents', 'Document')
        documents = Document.objects.filter(id__in=document_ids, user=user)

        logger.info(f"found {documents.count()} documents to process")

        for document in documents:
            logger.info(f"processing document {document.id}: {document.title}")
            try:
                # extract and chunk document content
                document_chunks, document_type = _extract_and_chunk_document(document)

                if document_chunks:
                    # store document embeddings
                    point_ids = embedding_service.store_document_embeddings(
                        user_id=user_id,
                        document_texts=document_chunks,
                        source=document_type,
                        document_id=str(document.id)  # pass document ID
                    )

                    results.append({
                        'document_id': document.id,
                        'success': bool(point_ids),
                        'chunks_created': len(point_ids),
                        'document_type': document_type
                    })

                    logger.info(f"embedded document {document.id} ({len(point_ids)} chunks)")
                else:
                    results.append({
                        'document_id': document.id,
                        'success': False,
                        'error': 'no content extracted'
                    })
                    logger.warning(f"no content for document {document.id}")

            except Exception as e:
                logger.error(f"failed to embed document {document.id}: {e}")
                results.append({
                    'document_id': document.id,
                    'success': False,
                    'error': str(e)
                })

        processing_time = time.time() - start_time
        successful_docs = sum(1 for r in results if r['success'])

        logger.info(f"batch embedding complete: user {user_id}: {successful_docs}/{len(results)} successful ({processing_time:.2f}s)")

        return {
            'success': True,
            'user_id': user_id,
            'processing_time': processing_time,
            'total_documents': len(results),
            'successful_documents': successful_docs,
            'results': results
        }

    except Exception as exc:
        logger.error(f"batch embedding failed: user {user_id}: {exc}")
        logger.error(f"full traceback: {traceback.format_exc()}")

        if self.request.retries < self.max_retries:
            logger.info(f"retrying batch document embedding for user {user_id}")
            raise self.retry(exc=exc, countdown=120)

        return {
            'success': False,
            'error': str(exc),
            'user_id': user_id,
            'processing_time': time.time() - start_time
        }


# helper functions
def _extract_user_profile(user) -> tuple[str, dict]:
    """extract profile text and metadata from user model including related academic_info and preferences"""
    logger.info(f"extracting complete profile for user {user.id} ({user.username})")

    try:
        # get user profile and related models
        profile = getattr(user, 'profile', None) or getattr(user, 'userprofile', None)
        academic_info = getattr(user, 'academic_info', None)
        preferences = getattr(user, 'preferences', None)

        logger.info(f"   profile: {profile}")
        logger.info(f"   academic_info: {academic_info}")
        logger.info(f"   preferences: {preferences}")

        # build comprehensive profile text
        profile_parts = []

        # basic user info
        if user.first_name or user.last_name:
            profile_parts.append(f"name: {user.first_name} {user.last_name}".strip())

        if user.email:
            profile_parts.append(f"email: {user.email}")

        # profile fields
        if profile:
            if hasattr(profile, 'phone_number') and profile.phone_number:
                profile_parts.append(f"phone: {profile.phone_number}")

            # use the full_name property if available
            if hasattr(profile, 'full_name'):
                full_name = profile.full_name
                if full_name and full_name != user.username:
                    profile_parts.append(f"full name: {full_name}")

        # academic information
        if academic_info:
            logger.info(f"   found academic info")

            if academic_info.high_school_name:
                profile_parts.append(f"high school: {academic_info.high_school_name}")

            if academic_info.graduation_year:
                profile_parts.append(f"graduation year: {academic_info.graduation_year}")

            if academic_info.gpa:
                scale = getattr(academic_info, 'gpa_scale', '4.0')
                profile_parts.append(f"gpa: {academic_info.gpa} on {scale} scale")

            # test scores
            test_scores = []
            if academic_info.sat_score:
                test_scores.append(f"sat: {academic_info.sat_score}")
            if academic_info.act_score:
                test_scores.append(f"act: {academic_info.act_score}")
            if academic_info.toefl_score:
                test_scores.append(f"toefl: {academic_info.toefl_score}")
            if academic_info.ielts_score:
                test_scores.append(f"ielts: {academic_info.ielts_score}")

            if test_scores:
                profile_parts.append(f"test scores: {', '.join(test_scores)}")

            # class rank
            if academic_info.class_rank and academic_info.class_size:
                profile_parts.append(f"class rank: {academic_info.class_rank} of {academic_info.class_size}")

        # application preferences
        if preferences:
            logger.info(f"   found preferences")

            if preferences.applying_for:
                profile_parts.append(f"applying for: {preferences.applying_for}")

            # fields of interest
            if preferences.fields_of_interest:
                if isinstance(preferences.fields_of_interest, list) and preferences.fields_of_interest:
                    interests = ', '.join(preferences.fields_of_interest)
                    profile_parts.append(f"fields of interest: {interests}")

            # financial aid
            aid_mapping = {0: 'none', 1: 'partial', 2: 'full'}
            if hasattr(preferences, 'need_financial_aid'):
                aid_level = aid_mapping.get(preferences.need_financial_aid, 'unknown')
                if aid_level != 'none':
                    profile_parts.append(f"financial aid needed: {aid_level}")

            # ranking preferences
            if hasattr(preferences, 'preferred_ranking_min') and hasattr(preferences, 'preferred_ranking_max'):
                min_rank = preferences.preferred_ranking_min
                max_rank = preferences.preferred_ranking_max
                if min_rank > 0 or max_rank < 500:
                    profile_parts.append(f"preferred school ranking: {min_rank}-{max_rank}")

        # build final profile text
        profile_text = ". ".join(profile_parts) if profile_parts else f"user profile for {user.username}"
        logger.info(f"   final profile text: {len(profile_text)} chars")
        logger.info(f"   profile text preview: {profile_text[:200]}...")

        # extract structured profile data for qdrant metadata
        profile_data = {
            "username": user.username,
            "email": user.email or '',
            "date_joined": user.date_joined.isoformat() if hasattr(user, 'date_joined') else ''
        }

        # basic profile info
        if profile:
            profile_data["phone"] = getattr(profile, 'phone_number', '') or ''
            profile_data["full_name"] = getattr(profile, 'full_name', '') or ''

        # academic data
        if academic_info:
            profile_data["degree"] = getattr(academic_info, 'applying_for', '') or ''  # will get from preferences
            profile_data["gpa"] = float(academic_info.gpa) if academic_info.gpa else 0.0
            profile_data["sat"] = int(academic_info.sat_score) if academic_info.sat_score else 0
            profile_data["high_school"] = getattr(academic_info, 'high_school_name', '') or ''
            profile_data["graduation_year"] = getattr(academic_info, 'graduation_year', '') or ''

            # additional test scores
            if academic_info.act_score:
                profile_data["act"] = int(academic_info.act_score)
            if academic_info.toefl_score:
                profile_data["toefl"] = int(academic_info.toefl_score)
            if academic_info.ielts_score:
                profile_data["ielts"] = float(academic_info.ielts_score)
        else:
            profile_data.update({"degree": "", "gpa": 0.0, "sat": 0, "high_school": "", "graduation_year": ""})

        # preferences data
        if preferences:
            profile_data["degree"] = getattr(preferences, 'applying_for', '') or ''  # override with preference

            # financial aid
            aid_mapping = {0: 'none', 1: 'partial', 2: 'full'}
            aid_level = aid_mapping.get(getattr(preferences, 'need_financial_aid', 0), 'none')
            profile_data["funding"] = aid_level

            # fields of interest
            interests = getattr(preferences, 'fields_of_interest', []) or []
            if isinstance(interests, list):
                profile_data["fields"] = [str(interest) for interest in interests if interest]
            else:
                profile_data["fields"] = []

            # ranking preferences
            profile_data["ranking_min"] = getattr(preferences, 'preferred_ranking_min', 0) or 0
            profile_data["ranking_max"] = getattr(preferences, 'preferred_ranking_max', 500) or 500
        else:
            profile_data.update({"funding": "", "fields": [], "ranking_min": 0, "ranking_max": 500})

        logger.info(f"   complete profile_data: {profile_data}")

        return profile_text, profile_data

    except Exception as e:
        logger.error(f"error extracting user profile for user {user.id}: {e}")
        logger.error(f"full traceback: {traceback.format_exc()}")
        return f"basic profile for user {user.username}", {
            "degree": "", "funding": "", "fields": [], "gpa": 0.0, "sat": 0,
            "username": user.username, "email": user.email or "", "phone": "", "full_name": ""
        }


def _extract_and_chunk_document(document) -> tuple[list, str]:
    """extract content from document and chunk it appropriately - UNCHANGED"""
    logger.info(f"extracting content from document {document.id}")

    try:
        # get document content based on type
        content = ""
        document_type = "unknown"

        # check for extracted text first (from OCR)
        if hasattr(document, 'extracted_text') and document.extracted_text:
            logger.info(f"   using extracted_text: {len(document.extracted_text)} chars")
            content = document.extracted_text
        # fallback to other fields
        elif hasattr(document, 'content') and document.content:
            logger.info(f"   using content field: {len(document.content)} chars")
            content = document.content
        elif hasattr(document, 'text') and document.text:
            logger.info(f"   using text field: {len(document.text)} chars")
            content = document.text
        elif hasattr(document, 'body') and document.body:
            logger.info(f"   using body field: {len(document.body)} chars")
            content = document.body
        else:
            # fallback to title if no content found (for testing)
            logger.warning(f"   no content found in any field, using title as fallback")
            content = f"Document: {document.title}. Type: {getattr(document, 'document_type', 'unknown')}. This document needs OCR processing to extract content."

        # determine document type
        if hasattr(document, 'document_type'):
            document_type = document.document_type
        elif hasattr(document, 'type'):
            document_type = document.type
        elif hasattr(document, 'category'):
            document_type = document.category
        else:
            # try to infer from filename or title
            name = getattr(document, 'name', '') or getattr(document, 'title', '') or getattr(document, 'filename', '')
            if 'sop' in name.lower() or 'statement' in name.lower():
                document_type = 'sop'
            elif 'lor' in name.lower() or 'recommendation' in name.lower():
                document_type = 'lor'
            elif 'transcript' in name.lower():
                document_type = 'transcript'
            elif 'resume' in name.lower() or 'cv' in name.lower():
                document_type = 'resume'
            else:
                document_type = 'document'

        logger.info(f"   document_type: {document_type}")
        logger.info(f"   content preview: {content[:200]}...")

        if not content or not content.strip():
            logger.warning(f"   empty content after extraction")
            return [], document_type

        # chunk the document content
        chunks = _chunk_text(content)
        logger.info(f"   created {len(chunks)} chunks")

        return chunks, document_type

    except Exception as e:
        logger.error(f"error extracting document content for document {document.id}: {e}")
        logger.error(f"full traceback: {traceback.format_exc()}")
        return [], "unknown"


def _chunk_text(text: str, max_chunk_size: int = 1000, overlap: int = 100) -> list:
    """chunk text into smaller pieces with optional overlap"""
    logger.info(f"chunking text: {len(text)} chars, max_size={max_chunk_size}")

    if not text or len(text) <= max_chunk_size:
        result = [text] if text else []
        logger.info(f"   no chunking needed: {len(result)} chunks")
        return result

    chunks = []
    words = text.split()
    current_chunk = []
    current_size = 0

    for word in words:
        word_size = len(word) + 1  # +1 for space

        if current_size + word_size > max_chunk_size and current_chunk:
            # save current chunk
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)

            # start new chunk with overlap
            if overlap > 0:
                overlap_words = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_words + [word]
                current_size = sum(len(w) + 1 for w in current_chunk)
            else:
                current_chunk = [word]
                current_size = word_size
        else:
            current_chunk.append(word)
            current_size += word_size

    # add final chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    logger.info(f"   chunking complete: {len(chunks)} chunks created")
    return chunks


# utility functions for testing and debugging
def inspect_user_chunks(user_id: int) -> dict:
    """inspect what chunks exist for a user"""
    try:
        embedding_service = get_embedding_service()
        if not embedding_service:
            return {'error': 'embedding service not available'}

        user_data = embedding_service.get_user_data(user_id)

        chunks_info = {}
        for chunk in user_data.get('profile_chunks', []):
            chunk_type = chunk.get('chunk_type', 'unknown')
            chunks_info[chunk_type] = {
                'id': chunk['id'],
                'category': chunk.get('chunk_category', ''),
                'text_length': len(chunk['data'].get('text', '')),
                'text_preview': chunk['data'].get('text', '')[:100] + '...',
                'created_at': chunk['data'].get('created_at', '')
            }

        return {
            'user_id': user_id,
            'total_profile_chunks': len(user_data.get('profile_chunks', [])),
            'total_documents': len(user_data.get('documents', [])),
            'chunk_details': chunks_info,
            'available_chunk_types': list(ProfileChunker.CHUNK_TYPES.keys())
        }

    except Exception as e:
        logger.error(f"failed to inspect chunks for user {user_id}: {e}")
        return {'error': str(e), 'user_id': user_id}


def trigger_complete_user_embedding(user_id: int, async_mode: bool = True):
    """trigger complete embedding for user profile + all documents"""
    logger.info(f"triggering complete embedding for user {user_id}")

    try:
        user = User.objects.get(id=user_id)
        Document = apps.get_model('documents', 'Document')
        user_documents = Document.objects.filter(user=user).values_list('id', flat=True)

        results = {}

        # trigger profile embedding
        logger.info(f"triggering profile embedding...")
        if async_mode:
            results['profile'] = embed_user_profile_task.delay(user_id)
        else:
            results['profile'] = embed_user_profile_task(user_id)

        # trigger document embeddings if user has documents
        if user_documents:
            logger.info(f"triggering {len(user_documents)} document embeddings...")
            if async_mode:
                results['documents'] = embed_multiple_documents_task.delay(user_id, list(user_documents))
            else:
                results['documents'] = embed_multiple_documents_task(user_id, list(user_documents))

        logger.info(f"triggered complete embedding for user {user_id} (profile + {len(user_documents)} docs)")
        return results

    except Exception as e:
        logger.error(f"failed to trigger complete embedding for user {user_id}: {e}")
        return {'error': str(e)}