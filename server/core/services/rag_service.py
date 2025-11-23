# server/messaging/rag_service.py - updated to use database storage
import time
from typing import List, Dict
from django.contrib.auth.models import User
from django.db import transaction
from core.services.embedding_service import get_embedding_service
from core.models import RAGChunk
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """retrieval augmented generation service with persistent database storage"""

    def __init__(self):
        self.embedding_service = get_embedding_service()

    def embed_user_profile(self, user: User) -> Dict:
        """embed user profile data with database persistence"""
        start_time = time.time()
        user_id = str(user.id)

        try:
            with transaction.atomic():
                # remove existing profile chunks
                RAGChunk.objects.filter(user=user, chunk_type='profile').delete()

                # build profile text
                profile_text = self._build_profile_text(user)
                if not profile_text:
                    logger.warning(f"⚠️ empty profile for user {user_id}")
                    return {'success': False, 'error': 'no profile data to embed'}

                # generate embedding
                embedding_result = self.embedding_service.generate_embedding(profile_text)

                # create and save chunk to database
                chunk = RAGChunk.objects.create(
                    id=f"profile_{user_id}",
                    user=user,
                    content=profile_text,
                    chunk_type='profile',
                    source='user_profile',
                    embedding=embedding_result['embedding'],
                    metadata={
                        'updated_at': time.time(),
                        'model': embedding_result['model'],
                        'cached': embedding_result.get('cached', False)
                    }
                )

                processing_time = time.time() - start_time
                logger.info(f"✅ profile embedded and saved to db for user {user_id} ({processing_time:.3f}s)")

                return {
                    'success': True,
                    'processing_time': processing_time,
                    'content_length': len(profile_text),
                    'model': embedding_result['model'],
                    'cached': embedding_result.get('cached', False)
                }

        except Exception as e:
            logger.error(f"❌ failed to embed profile for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}

    def embed_document(self, user: User, document) -> Dict:
        """embed document content with smart chunking and database persistence"""
        start_time = time.time()
        user_id = str(user.id)
        document_id = str(document.id)

        try:
            with transaction.atomic():
                # remove existing chunks for this document
                RAGChunk.objects.filter(
                    user=user,
                    chunk_type='document',
                    metadata__document_id=document_id
                ).delete()

                # create document chunks
                document_chunks = self._create_document_chunks(document)
                if not document_chunks:
                    logger.warning(f"⚠️ no content to embed for document {document_id}")
                    return {'success': False, 'error': 'no document content to embed'}

                # generate embeddings for all chunks
                chunk_texts = [chunk['content'] for chunk in document_chunks]
                embedding_results = self.embedding_service.generate_batch_embeddings(chunk_texts)

                # create and save memory chunks to database
                created_chunks = []
                for i, (doc_chunk, embedding_result) in enumerate(zip(document_chunks, embedding_results)):
                    chunk = RAGChunk.objects.create(
                        id=f"doc_{document_id}_chunk_{i}",
                        user=user,
                        content=doc_chunk['content'],
                        chunk_type='document',
                        source=document.document_type,
                        embedding=embedding_result['embedding'],
                        metadata={
                            'document_id': document_id,
                            'document_type': document.document_type,
                            'document_title': document.title,
                            'chunk_index': i,
                            'total_chunks': len(document_chunks),
                            'updated_at': time.time(),
                            'model': embedding_result['model'],
                            'cached': embedding_result.get('cached', False),
                            **doc_chunk.get('metadata', {})
                        }
                    )
                    created_chunks.append(chunk)

                processing_time = time.time() - start_time
                logger.info(f"✅ document {document_id} embedded and saved to db ({len(created_chunks)} chunks, {processing_time:.3f}s)")

                return {
                    'success': True,
                    'chunks_created': len(created_chunks),
                    'processing_time': processing_time,
                    'document_id': document_id,
                    'document_type': document.document_type
                }

        except Exception as e:
            logger.error(f"❌ failed to embed document {document_id}: {e}")
            return {'success': False, 'error': str(e)}

    def retrieve_context(self, user: User, query: str, top_k: int = 5) -> Dict:
        """retrieve relevant context for a query from database"""
        start_time = time.time()
        user_id = str(user.id)

        try:
            # get user's chunks from database
            user_chunks = RAGChunk.objects.filter(user=user).exclude(embedding__isnull=True)

            if not user_chunks.exists():
                logger.info(f"⚠️ no chunks found in db for user {user_id}")
                return {
                    'contexts': [],
                    'has_context': False,
                    'processing_time': time.time() - start_time
                }

            # generate query embedding
            query_embedding_result = self.embedding_service.generate_embedding(query)
            query_embedding = query_embedding_result['embedding']

            # calculate similarities and rank
            chunk_similarities = []
            for chunk in user_chunks:
                similarity = self.embedding_service.calculate_similarity(
                    query_embedding, chunk.embedding
                )
                chunk_similarities.append((chunk, similarity))

            # sort by similarity and take top k
            chunk_similarities.sort(key=lambda x: x[1], reverse=True)
            top_chunks = chunk_similarities[:top_k]

            # format contexts
            contexts = []
            for chunk, similarity in top_chunks:
                contexts.append({
                    'content': chunk.content,
                    'type': chunk.chunk_type,
                    'source': chunk.source,
                    'similarity': similarity,
                    'metadata': chunk.metadata
                })

            processing_time = time.time() - start_time
            logger.info(f"📊 retrieved {len(contexts)} contexts from db for user {user_id} ({processing_time:.3f}s)")

            return {
                'contexts': contexts,
                'has_context': len(contexts) > 0,
                'processing_time': processing_time,
                'query_embedding_cached': query_embedding_result.get('cached', False)
            }

        except Exception as e:
            logger.error(f"❌ context retrieval failed for user {user_id}: {e}")
            return {
                'contexts': [],
                'has_context': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }

    def build_contextual_prompt(self, user: User, query: str, max_context_length: int = 3000) -> Dict:
        """build contextualized prompt for ai using database context"""
        retrieval_result = self.retrieve_context(user, query)

        if not retrieval_result['has_context']:
            return {
                'system_prompt': self._get_default_system_prompt(),
                'user_prompt': query,
                'contexts_used': [],
                'has_context': False,
                'processing_time': retrieval_result['processing_time']
            }

        # build context text
        contexts = retrieval_result['contexts']
        context_parts = []
        current_length = 0
        contexts_used = []

        for ctx in contexts:
            context_text = f"[{ctx['type']}] {ctx['content']}"
            if current_length + len(context_text) > max_context_length:
                break
            context_parts.append(context_text)
            contexts_used.append({
                'type': ctx['type'],
                'source': ctx['source'],
                'similarity': ctx['similarity']
            })
            current_length += len(context_text)

        context_text = '\n\n'.join(context_parts)

        system_prompt = f"""you are a college application advisor. use this information about the student to provide personalized advice:

STUDENT CONTEXT:
{context_text}

provide specific advice based on the student's actual profile and documents. reference their stats and information when relevant. be conversational but professional. use lowercase and a friendly tone."""

        return {
            'system_prompt': system_prompt,
            'user_prompt': query,
            'contexts_used': contexts_used,
            'has_context': True,
            'context_length': len(context_text),
            'processing_time': retrieval_result['processing_time']
        }

    def _build_profile_text(self, user: User) -> str:
        """build text representation of user profile"""
        parts = [f"student: {user.first_name or 'student'}"]

        try:
            # academic info
            if hasattr(user, 'academic_info') and user.academic_info:
                academic = user.academic_info
                if academic.gpa:
                    parts.append(f"gpa: {academic.gpa}/{academic.gpa_scale}")
                if academic.graduation_year:
                    parts.append(f"graduation year: {academic.graduation_year}")
                if academic.sat_score:
                    parts.append(f"sat score: {academic.sat_score}")
                if academic.act_score:
                    parts.append(f"act score: {academic.act_score}")
                if academic.toefl_score:
                    parts.append(f"toefl score: {academic.toefl_score}")
                if academic.class_rank and academic.class_size:
                    parts.append(f"class rank: {academic.class_rank} out of {academic.class_size}")
                if academic.high_school_name:
                    parts.append(f"high school: {academic.high_school_name}")

            # preferences
            if hasattr(user, 'preferences') and user.preferences:
                prefs = user.preferences
                if prefs.fields_of_interest:
                    parts.append(f"interests: {', '.join(prefs.fields_of_interest)}")
                parts.append(f"applying for: {prefs.applying_for}")
                if prefs.need_financial_aid:
                    aid_levels = {1: 'partial', 2: 'full'}
                    parts.append(f"financial aid needed: {aid_levels.get(prefs.need_financial_aid, 'none')}")
                if prefs.preferred_ranking_min and prefs.preferred_ranking_max:
                    parts.append(f"target university ranking: {prefs.preferred_ranking_min}-{prefs.preferred_ranking_max}")

        except Exception as e:
            logger.warning(f"⚠️ error building profile for user {user.id}: {e}")

        return '. '.join(parts) if len(parts) > 1 else ""

    def _create_document_chunks(self, document) -> List[Dict]:
        """create smart chunks from document"""
        base_text = self._document_to_text(document)

        if not base_text or len(base_text) < 50:
            return []

        # for smaller documents, use single chunk
        if len(base_text) <= 1000:
            return [{'content': base_text, 'metadata': {'chunk_type': 'full_document'}}]

        # smart chunking based on document type
        doc_type = getattr(document, 'document_type', 'other')

        if doc_type == 'transcript':
            return self._chunk_transcript(document, base_text)
        elif doc_type in ['recommendation', 'essay']:
            return self._chunk_by_paragraphs(base_text, max_chunk_size=800)
        else:
            return self._chunk_generic(base_text)

    def _document_to_text(self, document) -> str:
        """convert document to text representation"""
        parts = [f"{document.document_type}: {document.title}"]

        # handle extracted text - could be string or dict
        if hasattr(document, 'extracted_text') and document.extracted_text:
            data = document.extracted_text

            # check if it's structured data (dict) or just raw text (string)
            if isinstance(data, dict):
                # structured data from ocr parsing
                if document.document_type == 'transcript':
                    if data.get('gpa'):
                        parts.append(f"transcript gpa: {data['gpa']}")
                    if data.get('courses'):
                        courses_text = self._format_courses(data['courses'])
                        if courses_text:
                            parts.append(f"courses: {courses_text}")

                elif document.document_type in ['sat_score', 'act_score', 'toefl_score']:
                    if data.get('total_score'):
                        parts.append(f"{document.document_type} total: {data['total_score']}")
                    if data.get('section_scores'):
                        sections = ', '.join(f"{k}: {v}" for k, v in data['section_scores'].items())
                        parts.append(f"sections: {sections}")

                elif data.get('text'):
                    # fallback to text field if available
                    parts.append(data['text'])

            elif isinstance(data, str):
                # raw text extracted from ocr
                parts.append(data)

            else:
                # unknown format, try to stringify
                parts.append(str(data))

        return '. '.join(parts)

    def _chunk_transcript(self, document, base_text: str) -> List[Dict]:
        """smart chunking for transcripts"""
        chunks = []

        # overall summary chunk
        chunks.append({
            'content': base_text,
            'metadata': {'chunk_type': 'transcript_summary'}
        })

        # if we have structured course data, create separate course chunk
        if hasattr(document, 'extracted_text') and isinstance(document.extracted_text, dict):
            if document.extracted_text.get('courses'):
                courses_text = self._format_courses(document.extracted_text['courses'])
                if courses_text and len(courses_text) > 100:
                    chunks.append({
                        'content': f"courses from {document.title}: {courses_text}",
                        'metadata': {'chunk_type': 'transcript_courses'}
                    })

        # if single chunk and too long, break it down further
        if len(chunks) == 1 and len(base_text) > 1000:
            return self._chunk_generic(base_text)

        return chunks

    def _chunk_by_paragraphs(self, text: str, max_chunk_size: int = 800) -> List[Dict]:
        """chunk text by paragraphs"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        if not paragraphs:
            return [{'content': text, 'metadata': {'chunk_type': 'single_chunk'}}]

        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            if current_size + len(para) > max_chunk_size and current_chunk:
                chunks.append({
                    'content': '\n\n'.join(current_chunk),
                    'metadata': {'chunk_type': 'paragraph_chunk'}
                })
                current_chunk = [para]
                current_size = len(para)
            else:
                current_chunk.append(para)
                current_size += len(para)

        # add final chunk
        if current_chunk:
            chunks.append({
                'content': '\n\n'.join(current_chunk),
                'metadata': {'chunk_type': 'paragraph_chunk'}
            })

        return chunks

    def _chunk_generic(self, text: str, max_chunk_size: int = 1000) -> List[Dict]:
        """generic text chunking"""
        if len(text) <= max_chunk_size:
            return [{'content': text, 'metadata': {'chunk_type': 'single_chunk'}}]

        # split by sentences
        sentences = [s.strip() + '.' for s in text.split('.') if s.strip()]
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            if current_size + len(sentence) > max_chunk_size and current_chunk:
                chunks.append({
                    'content': ' '.join(current_chunk),
                    'metadata': {'chunk_type': 'sentence_chunk'}
                })
                current_chunk = [sentence]
                current_size = len(sentence)
            else:
                current_chunk.append(sentence)
                current_size += len(sentence)

        # add final chunk
        if current_chunk:
            chunks.append({
                'content': ' '.join(current_chunk),
                'metadata': {'chunk_type': 'sentence_chunk'}
            })

        return chunks

    def _format_courses(self, courses) -> str:
        """format course data for embedding"""
        if not courses or not isinstance(courses, list):
            return ""

        course_texts = []
        for course in courses[:20]:  # limit to first 20 courses
            if isinstance(course, dict):
                name = course.get('name', 'Unknown Course')
                grade = course.get('grade', 'N/A')
                credits = course.get('credits', '')
                course_text = f"{name}: {grade}"
                if credits:
                    course_text += f" ({credits} credits)"
                course_texts.append(course_text)

        return '. '.join(course_texts)

    def _get_default_system_prompt(self) -> str:
        """default system prompt when no context available"""
        return """you are a college application advisor. the user hasn't provided much information yet, so ask them about their academic background and goals to provide better personalized advice. focus on understanding their gpa, test scores, intended major, and target universities."""

    def get_user_stats(self, user: User) -> Dict:
        """get rag statistics for user from database"""
        user_chunks = RAGChunk.objects.filter(user=user)

        stats = {
            'total_chunks': user_chunks.count(),
            'profile_chunks': user_chunks.filter(chunk_type='profile').count(),
            'document_chunks': user_chunks.filter(chunk_type='document').count(),
            'unique_documents': len(set(
                chunk.metadata.get('document_id')
                for chunk in user_chunks
                if chunk.metadata.get('document_id')
            )),
            'last_update': user_chunks.order_by('-updated_at').first().updated_at if user_chunks.exists() else None
        }

        return stats

    def clear_user_data(self, user: User) -> bool:
        """clear all rag data for user from database"""
        deleted_count, _ = RAGChunk.objects.filter(user=user).delete()
        if deleted_count > 0:
            logger.info(f"🗑️ cleared {deleted_count} rag chunks from db for user {user.id}")
            return True
        return False

    def test_context_retrieval(self, user: User, query: str = "what is my gpa?") -> Dict:
        """test method to see if context retrieval works"""
        try:
            # get user chunks
            user_chunks = RAGChunk.objects.filter(user=user)

            if not user_chunks.exists():
                return {
                    'status': 'no_chunks',
                    'message': f'no chunks found for user {user.id}',
                    'chunks_count': 0
                }

            # test retrieval
            result = self.retrieve_context(user, query, top_k=3)

            return {
                'status': 'success',
                'query': query,
                'chunks_found': user_chunks.count(),
                'contexts_retrieved': len(result['contexts']),
                'has_context': result['has_context'],
                'processing_time': result['processing_time'],
                'top_contexts': [
                    {
                        'type': ctx['type'],
                        'source': ctx['source'],
                        'similarity': ctx['similarity'],
                        'content_preview': ctx['content'][:200] + '...' if len(ctx['content']) > 200 else ctx['content']
                    }
                    for ctx in result['contexts'][:3]
                ]
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

# singleton instance
rag_service = RAGService()