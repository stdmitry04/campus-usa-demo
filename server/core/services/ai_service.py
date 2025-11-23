# server/core/services/ai_service.py - UPDATED FOR CHUNKED EMBEDDINGS
import time
from openai import OpenAI
from django.conf import settings
from django.contrib.auth.models import User
from typing import List, Dict, Optional
from core.services.embedding_service import get_embedding_service  # updated import path
import logging

logger = logging.getLogger(__name__)

class CollegeApplicationAI:
    """ai service that orchestrates rag retrieval and llm generation - UPDATED FOR CHUNKS"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_service = get_embedding_service()

        self.base_system_prompt = """you are an expert college application advisor specializing in US universities, admissions, and F-1 student visa processes. you help international students with:

1. university selection and rankings
2. application requirements and deadlines  
3. standardized tests (SAT, ACT, TOEFL, IELTS)
4. essays and personal statements
5. financial aid and scholarships
6. F-1 student visa application process
7. required documents for both admissions and visa
8. interview preparation

provide specific, actionable advice. when discussing requirements, be precise about deadlines, score ranges, and document specifications.

keep responses concise but comprehensive. use lowercase and a friendly, approachable tone."""

        self.fallback_knowledge = self._load_fallback_knowledge()

    def generate_response(self, user_message: str, conversation_history: List[Dict] = None,
                          user: Optional[User] = None, use_rag: bool = True,
                          top_k_documents: int = 5, include_profile: bool = True) -> Dict:
        """generate response with top-k chunk retrieval - UPDATED FOR CHUNKS"""
        start_time = time.time()

        try:
            # check if we can use rag
            if use_rag and user and self.embedding_service:
                logger.info(f"generating rag response for user {user.id} (top_k={top_k_documents}, profile={include_profile})")
                return self._generate_rag_response(
                    user_message, conversation_history, user, start_time,
                    top_k_documents, include_profile
                )
            else:
                reason = "no user" if not user else "embedding service unavailable" if not self.embedding_service else "rag disabled"
                logger.info(f"using fallback response: {reason}")

            # fallback to non-rag response
            return self._generate_fallback_response(user_message, conversation_history, start_time)

        except Exception as e:
            logger.error(f"ai response generation failed: {e}")
            response_time = time.time() - start_time

            return {
                'content': self._get_emergency_fallback(user_message),
                'response_time': response_time,
                'model_used': 'emergency_fallback',
                'success': False,
                'error': str(e),
                'rag_used': False
            }

    def _generate_rag_response(self, user_message: str, conversation_history: List[Dict],
                               user: User, start_time: float, top_k_documents: int,
                               include_profile: bool) -> Dict:
        """generate response using retrieved chunks - UPDATED FOR PROFILE CHUNKS"""
        try:
            # retrieve relevant content using embedding service (updated method)
            retrieval_start = time.time()

            context_results = self.embedding_service.search_user_context(
                user_id=user.id,
                query_text=user_message,
                top_k_documents=top_k_documents,
                include_profile=include_profile
            )

            retrieval_time = time.time() - retrieval_start

            # build contextual prompt with retrieved content (updated for chunks)
            system_prompt, user_prompt, context_stats = self._build_contextual_prompt(
                user_message, context_results, user
            )

            # build messages for openai
            messages = [{"role": "system", "content": system_prompt}]

            # add conversation history
            if conversation_history:
                for message in conversation_history[-8:]:
                    role = "user" if message.get('sender') == 'user' else "assistant"
                    messages.append({
                        "role": role,
                        "content": message.get('content', '')
                    })

            # add current user message
            messages.append({"role": "user", "content": user_prompt})

            # generate response with llm
            llm_start = time.time()
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            llm_time = time.time() - llm_start

            ai_response = response.choices[0].message.content
            total_time = time.time() - start_time

            logger.info(f"rag response generated (total: {total_time:.3f}s, retrieval: {retrieval_time:.3f}s, llm: {llm_time:.3f}s)")

            return {
                'content': ai_response,
                'response_time': total_time,
                'model_used': 'gpt-4o',
                'success': True,
                'rag_used': True,
                'rag_stats': {
                    'retrieval_time': retrieval_time,
                    'llm_time': llm_time,
                    'document_chunks_retrieved': len(context_results['documents']),
                    'profile_chunks_retrieved': len(context_results.get('profile_chunks', [])),  # updated
                    'total_context_length': context_stats['total_length'],
                    'document_sources': [doc['source'] for doc in context_results['documents']],
                    'chunk_scores': [doc['score'] for doc in context_results['documents']],
                    'chunk_lengths': [doc.get('text_length', len(doc.get('text', ''))) for doc in context_results['documents']],
                    'profile_chunk_types': [chunk['chunk_type'] for chunk in context_results.get('profile_chunks', [])],  # new
                    'top_k_documents': top_k_documents,
                    'include_profile': include_profile,
                    'context_stats': context_stats
                },
                'usage': {
                    'total_tokens': response.usage.total_tokens,
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens
                }
            }

        except Exception as e:
            logger.warning(f"rag response failed, falling back: {e}")
            import traceback
            logger.error(f"full traceback: {traceback.format_exc()}")
            return self._generate_fallback_response(user_message, conversation_history, start_time)

    def _build_contextual_prompt(self, user_message: str, context_results: Dict,
                                 user: User) -> tuple[str, str, Dict]:
        """build contextual prompt with retrieved content"""
        context_parts = []
        total_length = 0

        # add profile chunk context
        profile_chunks = context_results.get('profile_chunks', [])
        if profile_chunks:
            profile_context = f"student profile for {user.username}:\n"

            # organize chunks by type for better presentation
            chunk_categories = {
                'basic_personal': 'basic information',
                'application_prefs': 'application preferences',
                'high_school': 'high school background',
                'test_scores': 'standardized test scores',
                'profile_summary': 'profile summary',
                'score_narrative': 'test performance analysis',
                'academic_standing': 'academic achievements',
                'university_match': 'university matching profile'
            }

            # group chunks by category for organized presentation
            organized_chunks = {}
            for chunk in profile_chunks:
                chunk_type = chunk.get('chunk_type', 'unknown')
                category = chunk_categories.get(chunk_type, chunk_type)
                organized_chunks[category] = chunk.get('text', '')

            # add organized profile information
            for category, text in organized_chunks.items():
                if text:
                    profile_context += f"\n{category}:\n{text}\n"

            context_parts.append(profile_context)
            total_length += len(profile_context)

            logger.info(f"added profile context from {len(profile_chunks)} chunks: {list(organized_chunks.keys())}")

        # add document contexts (unchanged)
        if context_results['documents']:
            doc_context = "relevant documents:\n\n"
            for i, doc in enumerate(context_results['documents'], 1):
                source = doc['source']
                chunk_idx = doc['chunk_index']
                score = doc['score']
                text = doc.get('text', '')
                text_length = doc.get('text_length', len(text))

                # truncate very long chunks for context
                if len(text) > 500:
                    text = text[:500] + "..."

                chunk_context = f"{i}. {source} (chunk {chunk_idx}, similarity: {score:.3f}, {text_length} chars):\n{text}\n\n"
                doc_context += chunk_context
                total_length += len(chunk_context)

            context_parts.append(doc_context)

        # build system prompt
        if context_parts:
            context_text = "\n".join(context_parts)
            system_prompt = f"""{self.base_system_prompt}

you have access to the student's profile and documents. use this information to provide personalized advice:

{context_text}

when referencing information from their documents or profile, be specific about what you found. tailor your advice to their academic background, goals, and interests."""
        else:
            system_prompt = self.base_system_prompt

        # build user prompt
        user_prompt = f"""student question: {user_message}

please provide personalized advice based on my profile and documents."""

        context_stats = {
            'total_length': total_length,
            'context_parts': len(context_parts),
            'has_profile_chunks': len(profile_chunks) > 0,
            'profile_chunk_count': len(profile_chunks),
            'has_documents': len(context_results['documents']) > 0,
            'document_count': len(context_results['documents'])
        }

        return system_prompt, user_prompt, context_stats

    def _generate_fallback_response(self, user_message: str, conversation_history: List[Dict],
                                    start_time: float) -> Dict:
        """generate response without rag context - UNCHANGED"""
        try:
            messages = [{"role": "system", "content": self.base_system_prompt}]

            # add conversation history
            if conversation_history:
                for message in conversation_history[-5:]:
                    role = "user" if message.get('sender') == 'user' else "assistant"
                    messages.append({
                        "role": role,
                        "content": message.get('content', '')
                    })

            # inject relevant fallback knowledge
            relevant_knowledge = self._get_relevant_fallback_knowledge(user_message)
            if relevant_knowledge:
                messages.append({
                    "role": "system",
                    "content": f"relevant information:\n{relevant_knowledge}"
                })

            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )

            ai_response = response.choices[0].message.content
            response_time = time.time() - start_time

            logger.info(f"fallback response generated ({response_time:.3f}s)")

            return {
                'content': ai_response,
                'response_time': response_time,
                'model_used': 'gpt-4o',
                'success': True,
                'rag_used': False,
                'fallback_knowledge_used': len(relevant_knowledge) > 0,
                'usage': {
                    'total_tokens': response.usage.total_tokens,
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens
                }
            }

        except Exception as e:
            logger.error(f"fallback response failed: {e}")
            response_time = time.time() - start_time
            return {
                'content': self._get_emergency_fallback(user_message),
                'response_time': response_time,
                'model_used': 'emergency_fallback',
                'success': False,
                'error': str(e),
                'rag_used': False
            }

    def _load_fallback_knowledge(self) -> Dict[str, str]:
        """load fallback knowledge for when rag context isn't available - UNCHANGED"""
        return {
            'university_requirements': """MIT Computer Science Program:
- minimum gpa 3.8+ recommended, sat math 750+, total 1550+
- application deadline: january 1st, admission rate: ~4% for cs
- essays focus on creativity, collaboration, technical problem-solving

Stanford Engineering:
- gpa 3.9+ typical, sat median: 1510, admission rate: ~5%
- holistic review emphasizing intellectual vitality and leadership
- "what matters to you and why" essay required

Harvard University:
- gpa 3.9+, sat median: 1520, need-blind for international students
- full financial aid for families earning <$65k annually""",

            'visa_info': """f-1 visa process:
1. receive i-20 from university after admission
2. pay sevis fee ($350) at fmjfee.com
3. complete ds-160 form online
4. schedule interview (6-8 weeks advance booking)
5. attend interview with all required documents

required documents:
- valid passport, i-20 form, ds-160 confirmation
- sevis fee receipt, financial proof ($60k+)
- academic transcripts, test scores, bank statements""",

            'financial_aid': """need-blind universities: harvard, yale, princeton, mit, amherst
- full aid for families earning <$65k-75k annually
- merit scholarships: duke, university of richmond, usc
- css profile required for private universities
- international students: limited aid at most schools""",

            'test_requirements': """sat targets: top 10 (1520+), top 25 (1480+), top 50 (1400+)
toefl: top schools require 100+, speaking 26+, writing 24+
alternative: ielts 7.5+ for top schools
test-optional: available but scores still recommended for international students""",

            'application_strategy': """school selection: 8-12 total (2-3 reach, 4-6 target, 2-3 safety)
deadlines: early decision/action (nov 1-15), regular decision (jan 1)
essays: avoid clichés, show character growth, 650 word limit
timeline: junior spring (tests), summer (essays), senior fall (submit)"""
        }

    def _get_relevant_fallback_knowledge(self, user_message: str) -> str:
        """extract relevant fallback knowledge based on keywords - UNCHANGED"""
        message_lower = user_message.lower()
        relevant_sections = []

        section_keywords = {
            'university_requirements': ['mit', 'stanford', 'harvard', 'requirements', 'gpa', 'sat', 'admission'],
            'visa_info': ['visa', 'f-1', 'f1', 'embassy', 'interview', 'documents', 'i-20'],
            'financial_aid': ['financial aid', 'scholarship', 'money', 'cost', 'tuition', 'need-blind'],
            'test_requirements': ['sat', 'toefl', 'ielts', 'test', 'score'],
            'application_strategy': ['apply', 'application', 'deadline', 'essay', 'early decision']
        }

        for section, keywords in section_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                if section in self.fallback_knowledge:
                    relevant_sections.append(self.fallback_knowledge[section])

        return '\n\n'.join(relevant_sections[:2])

    def _get_emergency_fallback(self, user_message: str) -> str:
        """emergency responses when everything fails - UNCHANGED"""
        message_lower = user_message.lower()

        if any(word in message_lower for word in ['visa', 'f-1', 'f1']):
            return """for f-1 student visa: you need i-20 from university, then pay sevis fee, complete ds-160, schedule embassy interview. bring passport, financial proof, transcripts. interview focuses on study plans and ties to home country."""

        elif any(word in message_lower for word in ['mit', 'stanford', 'harvard']):
            return """top universities like mit, stanford, harvard require 3.8+ gpa, 1500+ sat, strong essays, and demonstrated excellence in your field. admission rates are 3-7%. need strong application strategy."""

        elif any(word in message_lower for word in ['financial aid', 'scholarship']):
            return """financial aid for international students: need-blind schools (harvard, yale, princeton, mit) offer full aid. most others have limited aid. merit scholarships available at some schools. css profile required."""

        else:
            return """i can help with university applications, visa processes, financial aid, test prep, and application strategy. what specific area interests you? please share your academic background so i can provide personalized advice."""

    def get_user_context_stats(self, user: User) -> Dict:
        """get statistics about available context for a user - UPDATED FOR CHUNKS"""
        if not self.embedding_service:
            return {'error': 'embedding service not available'}

        try:
            user_data = self.embedding_service.get_user_data(user.id)

            # analyze profile chunks
            profile_chunks = user_data.get('profile_chunks', [])
            chunk_breakdown = {}
            for chunk in profile_chunks:
                chunk_type = chunk.get('chunk_type', 'unknown')
                chunk_breakdown[chunk_type] = chunk_breakdown.get(chunk_type, 0) + 1

            return {
                'has_profile_chunks': len(profile_chunks) > 0,
                'profile_chunk_count': len(profile_chunks),
                'profile_chunk_types': list(chunk_breakdown.keys()),
                'profile_chunk_breakdown': chunk_breakdown,
                'document_chunks': len(user_data['documents']),
                'document_sources': list(set(doc['source'] for doc in user_data['documents'])),
                'total_chunks': len(user_data['documents']) + len(profile_chunks),
                # legacy compatibility
                'has_profile': len(profile_chunks) > 0
            }
        except Exception as e:
            logger.error(f"failed to get user context stats: {e}")
            return {'error': str(e)}

    def test_user_context(self, user: User, test_query: str = "what universities should i apply to") -> Dict:
        """test what context is available for a user - NEW DEBUG METHOD"""
        if not self.embedding_service:
            return {'error': 'embedding service not available'}

        try:
            # get context like the AI would
            context_results = self.embedding_service.search_user_context(
                user_id=user.id,
                query_text=test_query,
                top_k_documents=3,
                include_profile=True
            )

            # analyze what we found
            profile_chunks = context_results.get('profile_chunks', [])
            documents = context_results.get('documents', [])

            return {
                'test_query': test_query,
                'profile_chunks_found': len(profile_chunks),
                'profile_chunk_details': [
                    {
                        'type': chunk.get('chunk_type'),
                        'category': chunk.get('chunk_category'),
                        'text_preview': chunk.get('text', '')[:100] + '...',
                        'score': chunk.get('score', 0)
                    }
                    for chunk in profile_chunks
                ],
                'document_chunks_found': len(documents),
                'document_details': [
                    {
                        'source': doc.get('source'),
                        'chunk_index': doc.get('chunk_index'),
                        'text_preview': doc.get('text', '')[:100] + '...',
                        'score': doc.get('score', 0)
                    }
                    for doc in documents
                ],
                'would_have_context': len(profile_chunks) > 0 or len(documents) > 0
            }

        except Exception as e:
            logger.error(f"failed to test user context: {e}")
            return {'error': str(e)}


# singleton pattern with lazy initialization
ai_service = None

def get_ai_service():
    """get ai service with lazy initialization"""
    global ai_service
    if ai_service is None:
        try:
            ai_service = CollegeApplicationAI()
            print("ai service initialized successfully with chunked embedding support")
        except Exception as e:
            print(f"ai service failed to initialize: {e}")
            return None
    return ai_service