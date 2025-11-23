# server/messaging/ai_service.py
import time
from openai import OpenAI
from django.conf import settings
from typing import List, Dict
import chromadb
from sentence_transformers import SentenceTransformer
import os


class CollegeApplicationAI:
    """ENHANCED version - your existing class with RAG added"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.system_prompt = """..."""  # existing prompt

        # RAG components
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.PersistentClient(path="./college_knowledge_db")
        self.knowledge_collection = self.chroma_client.get_or_create_collection("college_guidance")

        # populate knowledge base on first run
        if self.knowledge_collection.count() == 0:
            self._populate_initial_knowledge()

    def generate_response(self, user_message: str, conversation_history=None, user_profile=None) -> Dict:
        """generates AI response with RAG enhancements"""
        start_time = time.time()

        try:
            # build context
            messages = self.get_conversation_context(conversation_history or [])

            # add user profile context
            if user_profile:
                profile_context = self._build_profile_context(user_profile)
                if profile_context:
                    messages.append({
                        "role": "system",
                        "content": f"user profile context: {profile_context}"
                    })

            retrieved_knowledge = self._retrieve_relevant_knowledge(user_message, user_profile)
            if retrieved_knowledge:
                knowledge_context = self._format_retrieved_knowledge(retrieved_knowledge)
                messages.append({
                    "role": "system",
                    "content": f"relevant information from knowledge base:\n{knowledge_context}"
                })

            # EXISTING: add user message and call openai (unchanged)
            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=800,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )

            ai_response = response.choices[0].message.content
            response_time = time.time() - start_time

            # ENHANCED: return metadata about knowledge used
            return {
                'content': ai_response,
                'response_time': response_time,
                'model_used': 'gpt-4',
                'knowledge_sources_used': len(retrieved_knowledge),  # NEW
                'success': True
            }

        except Exception as e:
            # EXISTING: your current error handling (unchanged)
            return self._handle_generation_error(e, user_message, start_time)

    # NEW: knowledge retrieval methods (add to your class)
    def _retrieve_relevant_knowledge(self, user_message: str, user_profile: dict = None, top_k: int = 3) -> list:
        """retrieve relevant knowledge from vector database"""
        try:
            # enhance query with user profile for better matching
            enhanced_query = user_message
            if user_profile:
                profile_keywords = self._extract_profile_keywords(user_profile)
                if profile_keywords:
                    enhanced_query += f" {' '.join(profile_keywords)}"

            # search knowledge base
            results = self.knowledge_collection.query(
                query_texts=[enhanced_query],
                n_results=top_k
            )

            # format results
            knowledge_docs = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    knowledge_docs.append({
                        'content': doc,
                        'source': metadata.get('source', 'knowledge base'),
                        'category': metadata.get('category', 'general')
                    })

            return knowledge_docs

        except Exception as e:
            print(f"knowledge retrieval failed: {e}")
            return []

    def _extract_profile_keywords(self, user_profile: dict) -> list:
        """extract keywords from user profile to improve retrieval"""
        keywords = []

        # academic level indicators
        academic = user_profile.get('academic_info', {})
        if academic.get('gpa', 0) >= 3.8:
            keywords.extend(['top universities', 'elite schools'])
        elif academic.get('gpa', 0) >= 3.5:
            keywords.extend(['competitive universities'])

        # field of interest
        preferences = user_profile.get('preferences', {})
        interests = preferences.get('fields_of_interest', [])
        keywords.extend(interests[:2])  # top 2 interests

        # degree level
        if preferences.get('applying_for') == 'bachelor':
            keywords.append('undergraduate')
        elif preferences.get('applying_for') in ['master', 'phd']:
            keywords.append('graduate')

        return keywords[:4]  # limit keywords

    def _format_retrieved_knowledge(self, knowledge_docs: list) -> str:
        """format retrieved knowledge for AI prompt"""
        if not knowledge_docs:
            return ""

        formatted_docs = []
        for doc in knowledge_docs:
            source = doc.get('source', 'unknown')
            content = doc.get('content', '')
            formatted_docs.append(f"[Source: {source}]\n{content}")

        return '\n\n'.join(formatted_docs)

    def _populate_initial_knowledge(self):
        """populate knowledge base with essential college application information"""
        print("🔄 populating knowledge base with college application guidance...")

        # essential knowledge for college applications
        knowledge_base = [
            {
                "content": "MIT Computer Science Program Requirements: Minimum GPA 3.8+ recommended, SAT Math 750+, strong programming background demonstrated through projects or competitions. Application deadline January 1st. Required essays focus on creativity, collaboration, and technical problem-solving. Admission rate approximately 4% for CS.",
                "metadata": {"source": "MIT Admissions", "category": "university_requirements",
                             "program": "computer_science"}
            },
            {
                "content": "Stanford Engineering Holistic Review: Academic excellence (GPA 3.9+ typical), intellectual vitality beyond grades, demonstrated leadership and entrepreneurial thinking. Average admitted SAT: 1510. Essays emphasize personal growth, impact, and 'What Matters to You and Why.' Admission rate 5% for engineering.",
                "metadata": {"source": "Stanford Admissions", "category": "university_requirements",
                             "program": "engineering"}
            },
            {
                "content": "F-1 Student Visa Interview Preparation: Schedule appointment 6-8 weeks in advance at US Embassy. Required documents: valid passport, Form I-20, DS-160 confirmation, SEVIS fee receipt, financial proof ($60,000+ for most universities), academic transcripts. Common interview questions: study plans, post-graduation intentions, ties to home country.",
                "metadata": {"source": "US State Department", "category": "visa_guidance", "type": "f1_interview"}
            },
            {
                "content": "Financial Aid for International Students: Need-blind universities (Harvard, Yale, Princeton, MIT, Amherst) consider international students for full financial aid. Merit-based aid more common at other universities. Deadlines typically match admission deadlines. CSS Profile required for most private universities. Expected family contribution calculated differently for international families.",
                "metadata": {"source": "College Board", "category": "financial_aid", "type": "international_students"}
            },
            {
                "content": "SAT Score Targets by University Tier: Top 10 universities (1520+ competitive), Top 25 universities (1480+ competitive), Top 50 universities (1400+ competitive). Test-optional policies at many universities post-2020, but scores still helpful for merit aid and international students. Subject tests discontinued but AP scores remain important.",
                "metadata": {"source": "College Board", "category": "test_requirements", "type": "sat_scoring"}
            },
            {
                "content": "TOEFL Requirements for International Students: Minimum 100+ for top universities, 90+ for most competitive programs. Speaking and Writing sections particularly important. IELTS alternative (7.5+ for top schools). Some universities waive English requirements for students from English-speaking countries or with SAT/ACT verbal scores above certain thresholds.",
                "metadata": {"source": "ETS", "category": "test_requirements", "type": "english_proficiency"}
            },
            {
                "content": "Common Application Essay Strategy: Personal statement should reveal character, values, and growth. Avoid generic topics (sports injury, volunteer trip) unless you have unique perspective. Show don't tell through specific examples. Word limit 650 words. Supplemental essays equally important - research each school's values and culture.",
                "metadata": {"source": "Common Application", "category": "essays", "type": "personal_statement"}
            },
            {
                "content": "Early Decision vs Early Action Strategy: Early Decision binding commitment increases admission chances 10-15% at most schools but limits financial aid comparison. Early Action non-binding with similar application timeline. Restrictive Early Action (REA) at Harvard, Stanford, Yale prohibits other early applications. Regular Decision allows full comparison of offers.",
                "metadata": {"source": "NACAC", "category": "application_strategy", "type": "admission_plans"}
            },
            {
                "content": "Letter of Recommendation Best Practices: Request from teachers who know you well, preferably in core academic subjects related to intended major. Provide recommenders with resume, personal statement draft, and specific accomplishments. Ask at least 2 months before deadline. Follow up politely if needed. Counselor recommendation required for most universities.",
                "metadata": {"source": "NACAC", "category": "recommendations", "type": "teacher_recommendations"}
            },
            {
                "content": "University Selection Strategy: Apply to 8-12 universities: 2-3 reach schools (admission rate <20%), 4-6 target schools (admission rate 20-50%), 2-3 safety schools (admission rate >50% and strong fit). Consider cost, location, program strength, research opportunities, campus culture. Visit virtually or in-person when possible.",
                "metadata": {"source": "College Counseling", "category": "application_strategy",
                             "type": "school_selection"}
            }
        ]

        # add to vector database
        documents = [item["content"] for item in knowledge_base]
        metadatas = [item["metadata"] for item in knowledge_base]
        ids = [f"knowledge_{i}" for i in range(len(knowledge_base))]

        self.knowledge_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        print(f"✅ added {len(knowledge_base)} knowledge documents to database")
