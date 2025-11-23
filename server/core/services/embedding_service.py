# server/messaging/embedding_service.py
import time
import hashlib
from typing import List, Dict, Optional, Any
from openai import OpenAI
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http import models
import uuid

logger = logging.getLogger(__name__)

# qdrant collection configuration per spec
COLLECTION_NAME = "user_data"
PROFILE_VECTOR_SIZE = 384  # for profile embeddings
DOCUMENT_VECTOR_SIZE = 768  # for document embeddings


class ProfileChunker:
    """handles splitting user profiles into semantic chunks"""

    # define chunk types that correspond to specific profile sections
    CHUNK_TYPES = {
        'basic_personal': 'basic personal information',
        'application_prefs': 'application preferences',
        'high_school': 'high school information',
        'test_scores': 'standardized test scores',
        'profile_summary': 'complete profile summary',
        'score_narrative': 'test score analysis',
        'academic_standing': 'academic achievement summary',
        'university_match': 'university matching profile'
    }

    def __init__(self, user_data: dict, profile_data: dict):
        """initialize with extracted user data"""
        self.user_data = user_data
        self.profile_data = profile_data
        self.chunks = {}

    def generate_all_chunks(self) -> Dict[str, str]:
        """create all profile chunks"""
        try:
            # generate each chunk type
            self.chunks['basic_personal'] = self._create_basic_personal_chunk()
            self.chunks['application_prefs'] = self._create_application_prefs_chunk()
            self.chunks['high_school'] = self._create_high_school_chunk()
            self.chunks['test_scores'] = self._create_test_scores_chunk()
            self.chunks['profile_summary'] = self._create_profile_summary_chunk()
            self.chunks['score_narrative'] = self._create_score_narrative_chunk()
            self.chunks['academic_standing'] = self._create_academic_standing_chunk()
            self.chunks['university_match'] = self._create_university_match_chunk()

            # filter out empty chunks
            self.chunks = {k: v for k, v in self.chunks.items() if v and v.strip()}

            return self.chunks

        except Exception as e:
            logger.error(f"failed to generate chunks: {str(e)}")
            return {}

    def _create_basic_personal_chunk(self) -> str:
        """basic contact and personal information"""
        parts = []

        # name info from user_data
        full_name = self.profile_data.get('full_name', '')
        username = self.user_data.get('username', '')
        if full_name and full_name != username:
            parts.append(f"student name: {full_name}")
        elif username:
            parts.append(f"username: {username}")

        # contact info
        email = self.user_data.get('email', '')
        if email:
            parts.append(f"email: {email}")

        phone = self.profile_data.get('phone', '')
        if phone:
            parts.append(f"phone: {phone}")

        return " | ".join(parts) if parts else ""

    def _create_application_prefs_chunk(self) -> str:
        """application preferences and requirements"""
        parts = []

        # degree type
        degree = self.profile_data.get('degree', '')
        if degree:
            parts.append(f"applying for: {degree}")

        # financial aid needs
        funding = self.profile_data.get('funding', 'none')
        if funding and funding != 'none':
            parts.append(f"financial aid needed: {funding}")

        # ranking preferences
        min_rank = self.profile_data.get('ranking_min', 0)
        max_rank = self.profile_data.get('ranking_max', 500)
        if min_rank > 0 or max_rank < 500:
            parts.append(f"preferred university ranking: {min_rank}-{max_rank}")

        # fields of interest
        fields = self.profile_data.get('fields', [])
        if fields and isinstance(fields, list):
            interests = ", ".join(fields)
            parts.append(f"fields of interest: {interests}")

        return " | ".join(parts)

    def _create_high_school_chunk(self) -> str:
        """high school academic information"""
        parts = []

        # school info
        high_school = self.profile_data.get('high_school', '')
        if high_school:
            parts.append(f"high school: {high_school}")

        grad_year = self.profile_data.get('graduation_year', '')
        if grad_year:
            parts.append(f"graduation year: {grad_year}")

        # gpa info
        gpa = self.profile_data.get('gpa', 0.0)
        if gpa > 0:
            parts.append(f"gpa: {gpa}")

        return " | ".join(parts)

    def _create_test_scores_chunk(self) -> str:
        """standardized test scores"""
        parts = []

        # main standardized tests
        sat = self.profile_data.get('sat', 0)
        if sat > 0:
            parts.append(f"sat: {sat}")

        act = self.profile_data.get('act', 0)
        if act > 0:
            parts.append(f"act: {act}")

        # english proficiency tests
        toefl = self.profile_data.get('toefl', 0)
        if toefl > 0:
            parts.append(f"toefl: {toefl}")

        ielts = self.profile_data.get('ielts', 0.0)
        if ielts > 0:
            parts.append(f"ielts: {ielts}")

        return " | ".join(parts)

    def _create_profile_summary_chunk(self) -> str:
        """comprehensive profile narrative"""
        parts = []

        # start with name
        name = self.profile_data.get('full_name', '') or self.user_data.get('username', 'student')
        parts.append(f"{name} is a student")

        # add application info
        degree = self.profile_data.get('degree', '')
        fields = self.profile_data.get('fields', [])
        if degree and fields:
            interests = " and ".join(fields[:2])  # first 2 interests
            parts.append(f"applying for a {degree} in {interests}")
        elif degree:
            parts.append(f"applying for a {degree}")

        # add academic background
        academic_parts = []

        high_school = self.profile_data.get('high_school', '')
        grad_year = self.profile_data.get('graduation_year', '')
        if high_school and grad_year:
            academic_parts.append(f"graduated from {high_school} in {grad_year}")

        gpa = self.profile_data.get('gpa', 0.0)
        if gpa > 0:
            academic_parts.append(f"with a {gpa} gpa")

        # test scores
        scores = []
        sat = self.profile_data.get('sat', 0)
        if sat > 0:
            scores.append(f"{sat} sat")
        act = self.profile_data.get('act', 0)
        if act > 0:
            scores.append(f"{act} act")
        if scores:
            academic_parts.append(f"scored {' and '.join(scores)}")

        if academic_parts:
            parts.extend(academic_parts)

        return ". ".join(parts) + "." if len(parts) > 1 else ""

    def _create_score_narrative_chunk(self) -> str:
        """narrative analysis of test performance"""
        analyses = []

        # sat analysis
        sat = self.profile_data.get('sat', 0)
        if sat > 0:
            if sat >= 1500:
                analyses.append(f"excellent sat performance with {sat} (top 1%)")
            elif sat >= 1400:
                analyses.append(f"strong sat score of {sat} (top 5%)")
            elif sat >= 1300:
                analyses.append(f"competitive sat score of {sat}")
            else:
                analyses.append(f"sat score: {sat}")

        # act analysis
        act = self.profile_data.get('act', 0)
        if act > 0:
            if act >= 34:
                analyses.append(f"outstanding act score of {act} (top 1%)")
            elif act >= 30:
                analyses.append(f"excellent act performance with {act}")
            elif act >= 25:
                analyses.append(f"solid act score of {act}")
            else:
                analyses.append(f"act score: {act}")

        # english proficiency
        toefl = self.profile_data.get('toefl', 0)
        if toefl > 0 and toefl >= 100:
            analyses.append(f"strong english proficiency with toefl {toefl}")
        elif toefl > 0:
            analyses.append(f"toefl score: {toefl}")

        ielts = self.profile_data.get('ielts', 0.0)
        if ielts > 0 and ielts >= 7.0:
            analyses.append(f"excellent ielts score of {ielts}")
        elif ielts > 0:
            analyses.append(f"ielts score: {ielts}")

        return " | ".join(analyses)

    def _create_academic_standing_chunk(self) -> str:
        """overall academic achievement summary"""
        achievements = []

        # gpa achievement
        gpa = self.profile_data.get('gpa', 0.0)
        if gpa > 0:
            if gpa >= 3.8:
                achievements.append(f"high academic achiever with {gpa} gpa")
            elif gpa >= 3.5:
                achievements.append(f"strong academic performance with {gpa} gpa")
            else:
                achievements.append(f"gpa: {gpa}")

        return " | ".join(achievements)

    def _create_university_match_chunk(self) -> str:
        """profile formatted for university matching queries"""
        parts = []

        # what kind of universities would accept this profile
        gpa = self.profile_data.get('gpa', 0.0)
        if gpa > 0:
            parts.append(f"gpa {gpa}")

        sat = self.profile_data.get('sat', 0)
        if sat > 0:
            parts.append(f"sat {sat}")

        act = self.profile_data.get('act', 0)
        if act > 0:
            parts.append(f"act {act}")

        degree = self.profile_data.get('degree', '')
        if degree:
            parts.append(f"seeking {degree}")

        fields = self.profile_data.get('fields', [])
        if fields:
            majors = ", ".join(fields)
            parts.append(f"interested in {majors}")

        funding = self.profile_data.get('funding', 'none')
        if funding and funding != "none":
            parts.append(f"needs {funding} financial aid")

        base = "university matching profile: " + " | ".join(parts)

        # add what universities to recommend
        if gpa >= 3.5:
            base += " | suitable for competitive universities"
        if (sat >= 1400) or (act >= 30):
            base += " | qualified for top-tier institutions"

        return base


class EmbeddingService:
    """handles text embedding generation, caching, and qdrant storage"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # different models for different embedding types per spec
        self.profile_model = "text-embedding-3-small"  # 384 dimensions when specified
        self.document_model = "text-embedding-3-large"  # 768 dimensions default

        self.max_tokens = 8191  # token limit for embedding model

        # initialize qdrant client
        self._init_qdrant()

        # ensure collection exists with correct configuration
        self._setup_user_data_collection()

    def _init_qdrant(self):
        """set up connection to qdrant vector database"""
        try:
            # local qdrant instance
            self.qdrant_client = QdrantClient(
                url=getattr(settings, 'QDRANT_URL', 'http://localhost:6333')
            )


            # test connection
            collections = self.qdrant_client.get_collections()
            logger.info(f"connected to qdrant successfully, found {len(collections.collections)} collections")

        except Exception as e:
            logger.error(f"failed to connect to qdrant: {e}")
            self.qdrant_client = None

    def _setup_user_data_collection(self):
        """create the user_data collection with named vectors per spec"""
        if not self.qdrant_client:
            logger.error("qdrant client not available")
            return False

        try:
            # recreate collection with named vectors
            if not self.qdrant_client.collection_exists(COLLECTION_NAME):
                self.qdrant_client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config={
                        "document": VectorParams(size=DOCUMENT_VECTOR_SIZE, distance=Distance.COSINE),
                        "profile": VectorParams(size=PROFILE_VECTOR_SIZE, distance=Distance.COSINE),
                    }
                )

            logger.info(f"created collection {COLLECTION_NAME} with named vectors")
            return True

        except Exception as e:
            logger.error(f"failed to create collection {COLLECTION_NAME}: {e}")
            return False

    def generate_profile_embedding(self, text: str, use_cache: bool = True) -> Dict:
        """generate profile embedding using smaller model (384 dimensions)"""
        return self._generate_embedding(
            text=text,
            model=self.profile_model,
            dimensions=PROFILE_VECTOR_SIZE,
            use_cache=use_cache,
            embedding_type="profile"
        )

    def generate_document_embedding(self, text: str, use_cache: bool = True) -> Dict:
        """generate document embedding using larger model (768 dimensions)"""
        return self._generate_embedding(
            text=text,
            model=self.document_model,
            dimensions=DOCUMENT_VECTOR_SIZE,
            use_cache=use_cache,
            embedding_type="document"
        )

    def _generate_embedding(self, text: str, model: str, dimensions: int, use_cache: bool, embedding_type: str) -> Dict:
        """internal method to generate embeddings with caching"""
        start_time = time.time()

        # validate input
        if not text or not text.strip():
            raise ValidationError("text cannot be empty")

        # clean and prepare text
        clean_text = self._prepare_text(text)

        # check cache first
        cache_key = self._get_cache_key(clean_text, model, dimensions)
        if use_cache:
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"using cached {embedding_type} embedding for text length {len(clean_text)}")
                return {
                    'embedding': cached_result['embedding'],
                    'model': cached_result['model'],
                    'dimensions': cached_result['dimensions'],
                    'type': embedding_type,
                    'cached': True,
                    'processing_time': time.time() - start_time
                }

        try:
            logger.info(f"generating {embedding_type} embedding for text ({len(clean_text)} chars)")

            # call openai embedding api
            response = self.client.embeddings.create(
                input=clean_text,
                model=model,
                dimensions=dimensions
            )

            embedding = response.data[0].embedding
            processing_time = time.time() - start_time

            # cache the result for 24 hours
            if use_cache:
                cache_data = {
                    'embedding': embedding,
                    'model': model,
                    'dimensions': dimensions
                }
                cache.set(cache_key, cache_data, 60 * 60 * 24)  # 24 hours

            logger.info(f"{embedding_type} embedding generated ({dimensions} dimensions, {processing_time:.3f}s)")

            return {
                'embedding': embedding,
                'model': model,
                'dimensions': dimensions,
                'type': embedding_type,
                'cached': False,
                'processing_time': processing_time,
                'usage': {
                    'total_tokens': response.usage.total_tokens,
                    'model': model
                }
            }

        except Exception as e:
            logger.error(f"{embedding_type} embedding generation failed: {e}")
            print(f"[EMBEDDING FAIL] {embedding_type} embedding failed: {e}")
            raise ValidationError(f"failed to generate {embedding_type} embedding: {str(e)}")


    # NEW: chunked profile embedding methods
    def store_chunked_profile_embeddings(self,
                                         user_id: int,
                                         user_data: dict,
                                         profile_data: dict) -> Dict[str, str]:
        """store profile as multiple chunks instead of single embedding"""
        if not self.qdrant_client:
            logger.error("qdrant client not available")
            return {}

        try:
            # clear existing profile chunks for this user
            self._clear_user_profile_chunks(user_id)

            # generate chunks
            chunker = ProfileChunker(user_data, profile_data)
            chunks = chunker.generate_all_chunks()

            if not chunks:
                logger.warning(f"no chunks generated for user {user_id}")
                return {}

            logger.info(f"generated {len(chunks)} profile chunks for user {user_id}")

            # embed and store each chunk
            points = []
            chunk_ids = {}

            for chunk_type, content in chunks.items():
                if content and content.strip():
                    # generate embedding for chunk
                    embedding_result = self.generate_profile_embedding(content)
                    chunk_vector = embedding_result['embedding']

                    # create point with chunk-specific metadata
                    point_id = str(uuid.uuid4())
                    chunk_ids[chunk_type] = point_id

                    point = PointStruct(
                        id=point_id,
                        vector={"profile": chunk_vector},
                        payload={
                            "user_id": user_id,
                            "type": "profile_chunk",
                            "chunk_type": chunk_type,
                            "chunk_category": ProfileChunker.CHUNK_TYPES.get(chunk_type, chunk_type),
                            "text": content,
                            "text_length": len(content),
                            # include original profile data for search filters
                            "degree": profile_data.get("degree", ""),
                            "funding": profile_data.get("funding", ""),
                            "fields": profile_data.get("fields", []),
                            "gpa": profile_data.get("gpa", 0.0),
                            "sat": profile_data.get("sat", 0),
                            "created_at": time.time(),
                            "chunk_user_key": f"user_{user_id}_chunk_{chunk_type}"
                        }
                    )
                    points.append(point)

            # batch store in qdrant
            if points:
                self.qdrant_client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points
                )
                logger.info(f"stored {len(points)} profile chunks for user {user_id}")

            return chunk_ids

        except Exception as e:
            logger.error(f"failed to store chunked profile for user {user_id}: {e}")
            return {}

    def update_specific_profile_chunks(self,
                                       user_id: int,
                                       user_data: dict,
                                       profile_data: dict,
                                       chunk_types: List[str]) -> Dict[str, str]:
        """update only specific profile chunks"""
        if not self.qdrant_client:
            return {}

        try:
            # generate all chunks but only update requested ones
            chunker = ProfileChunker(user_data, profile_data)
            all_chunks = chunker.generate_all_chunks()

            chunks_to_update = {k: v for k, v in all_chunks.items() if k in chunk_types}

            if not chunks_to_update:
                logger.warning(f"no chunks to update for user {user_id}, types: {chunk_types}")
                return {}

            # clear existing chunks of these types
            for chunk_type in chunk_types:
                self._clear_user_chunk_type(user_id, chunk_type)

            # create new points for updated chunks
            points = []
            chunk_ids = {}

            for chunk_type, content in chunks_to_update.items():
                if content and content.strip():
                    embedding_result = self.generate_profile_embedding(content)
                    chunk_vector = embedding_result['embedding']

                    point_id = str(uuid.uuid4())
                    chunk_ids[chunk_type] = point_id

                    point = PointStruct(
                        id=point_id,
                        vector={"profile": chunk_vector},
                        payload={
                            "user_id": user_id,
                            "type": "profile_chunk",
                            "chunk_type": chunk_type,
                            "chunk_category": ProfileChunker.CHUNK_TYPES.get(chunk_type, chunk_type),
                            "text": content,
                            "text_length": len(content),
                            "degree": profile_data.get("degree", ""),
                            "funding": profile_data.get("funding", ""),
                            "fields": profile_data.get("fields", []),
                            "gpa": profile_data.get("gpa", 0.0),
                            "sat": profile_data.get("sat", 0),
                            "created_at": time.time(),
                            "chunk_user_key": f"user_{user_id}_chunk_{chunk_type}"
                        }
                    )
                    points.append(point)

            if points:
                self.qdrant_client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points
                )
                logger.info(f"updated {len(points)} profile chunks for user {user_id}: {list(chunks_to_update.keys())}")

            return chunk_ids

        except Exception as e:
            logger.error(f"failed to update profile chunks for user {user_id}: {e}")
            return {}

    def _clear_user_profile_chunks(self, user_id: int):
        """remove all existing profile chunks for a user"""
        try:
            self.qdrant_client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                            FieldCondition(key="type", match=MatchValue(value="profile_chunk"))
                        ]
                    )
                )
            )
            logger.info(f"cleared existing profile chunks for user {user_id}")
        except Exception as e:
            logger.warning(f"failed to clear profile chunks for user {user_id}: {str(e)}")

    def _clear_user_chunk_type(self, user_id: int, chunk_type: str):
        """remove specific chunk type for a user"""
        try:
            self.qdrant_client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                            FieldCondition(key="type", match=MatchValue(value="profile_chunk")),
                            FieldCondition(key="chunk_type", match=MatchValue(value=chunk_type))
                        ]
                    )
                )
            )
            logger.info(f"cleared {chunk_type} chunk for user {user_id}")
        except Exception as e:
            logger.warning(f"failed to clear {chunk_type} chunk for user {user_id}: {str(e)}")

    # keep existing methods for backward compatibility
    def store_profile_embedding(self,
                                user_id: int,
                                profile_text: str,
                                profile_data: Dict) -> bool:
        """store profile embedding per spec format with UUID point ID - LEGACY METHOD"""
        # this is now a wrapper around chunked embedding
        user_data = {
            'username': profile_data.get('username', ''),
            'email': profile_data.get('email', '')
        }

        chunk_ids = self.store_chunked_profile_embeddings(user_id, user_data, profile_data)
        return bool(chunk_ids)

    def store_document_embeddings(self,
                                  user_id: int,
                                  document_texts: List[str],
                                  source: str,
                                  document_id: str = None) -> List[str]:
        """store document embeddings per spec format with UUID point IDs"""
        if not self.qdrant_client or not document_texts:
            return []

        try:
            points = []
            point_ids = []

            for i, doc_text in enumerate(document_texts):
                # generate document embedding
                embedding_result = self.generate_document_embedding(doc_text)
                doc_vector = embedding_result['embedding']

                # create UUID point ID
                point_id = str(uuid.uuid4())
                point_ids.append(point_id)

                # create point with spec-compliant format using UUID
                point = PointStruct(
                    id=point_id,
                    vector={"document": doc_vector},
                    payload={
                        "user_id": user_id,
                        "type": "document",
                        "source": source,
                        "chunk_index": i,
                        "text": doc_text,  # store original text for retrieval
                        "text_length": len(doc_text),
                        "created_at": time.time(),
                        "document_user_key": f"user_{user_id}_doc_{i}",
                        "document_id": document_id
                    }
                )
                points.append(point)

            # batch upload to qdrant
            self.qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )

            logger.info(f"stored {len(points)} document embeddings for user {user_id} from {source}")
            return point_ids

        except Exception as e:
            logger.error(f"failed to store document embeddings for user {user_id}: {e}")
            return []

    def search_user_documents(self,
                              user_id: int,
                              query_text: str,
                              limit: int = 10) -> List[Dict]:
        """search user's documents using document embedding and return original text"""
        if not self.qdrant_client:
            return []

        try:
            # generate document embedding for query
            embedding_result = self.generate_document_embedding(query_text)
            query_vector = embedding_result['embedding']

            # use query_points instead of search for modern api
            search_results = self.qdrant_client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                using="document",
                limit=limit,
                query_filter=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                        FieldCondition(key="type", match=MatchValue(value="document"))
                    ]
                )
            )

            # format results with original text
            results = []
            for point in search_results.points:
                results.append({
                    'id': point.id,
                    'score': point.score,
                    'source': point.payload.get('source', ''),
                    'chunk_index': point.payload.get('chunk_index', 0),
                    'text': point.payload.get('text', ''),  # original text for gpt
                    'text_length': point.payload.get('text_length', 0),
                    'metadata': point.payload
                })

            logger.info(f"found {len(results)} document matches for user {user_id}")
            return results

        except Exception as e:
            logger.error(f"document search failed for user {user_id}: {e}")
            return []

    def search_user_profile_chunks(self,
                                   user_id: int,
                                   query_text: str,
                                   chunk_types: List[str] = None,
                                   limit: int = 5) -> List[Dict]:
        """search user's profile chunks"""
        if not self.qdrant_client:
            return []

        try:
            # generate profile embedding for query
            embedding_result = self.generate_profile_embedding(query_text)
            query_vector = embedding_result['embedding']

            # build filter
            filter_conditions = [
                FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                FieldCondition(key="type", match=MatchValue(value="profile_chunk"))
            ]

            # optionally filter by chunk types
            if chunk_types:
                filter_conditions.append(
                    FieldCondition(key="chunk_type", match=MatchValue(value=chunk_types))
                )

            search_results = self.qdrant_client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                using="profile",
                limit=limit,
                query_filter=Filter(must=filter_conditions)
            )

            # format results
            results = []
            for point in search_results.points:
                results.append({
                    'id': point.id,
                    'score': point.score,
                    'chunk_type': point.payload.get('chunk_type', ''),
                    'chunk_category': point.payload.get('chunk_category', ''),
                    'text': point.payload.get('text', ''),
                    'text_length': point.payload.get('text_length', 0),
                    'metadata': point.payload
                })

            logger.info(f"found {len(results)} profile chunk matches for user {user_id}")
            return results

        except Exception as e:
            logger.error(f"profile chunk search failed for user {user_id}: {e}")
            return []

    def search_user_context(self,
                            user_id: int,
                            query_text: str,
                            top_k_documents: int = 5,
                            include_profile: bool = True) -> Dict:
        """search user's documents and profile in one call for ai context - UPDATED FOR CHUNKS"""
        if not self.qdrant_client:
            return {"documents": [], "profile_chunks": []}

        try:
            results = {"documents": [], "profile_chunks": []}

            # search documents (unchanged)
            if top_k_documents > 0:
                query_vector = self.generate_document_embedding(query_text)['embedding']

                doc_search = self.qdrant_client.query_points(
                    collection_name=COLLECTION_NAME,
                    query=query_vector,
                    using="document",
                    limit=top_k_documents,
                    query_filter=Filter(
                        must=[
                            FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                            FieldCondition(key="type", match=MatchValue(value="document"))
                        ]
                    )
                )

                for point in doc_search.points:
                    results["documents"].append({
                        'id': point.id,
                        'score': point.score,
                        'source': point.payload.get('source', ''),
                        'chunk_index': point.payload.get('chunk_index', 0),
                        'text': point.payload.get('text', ''),
                        'text_length': point.payload.get('text_length', 0)
                    })

            # search profile chunks (new)
            if include_profile:
                profile_chunks = self.search_user_profile_chunks(
                    user_id=user_id,
                    query_text=query_text,
                    limit=3  # get top 3 most relevant chunks
                )
                results["profile_chunks"] = profile_chunks

            logger.info(f"retrieved context for user {user_id}: {len(results['documents'])} docs, {len(results['profile_chunks'])} profile chunks")
            return results

        except Exception as e:
            logger.error(f"context search failed for user {user_id}: {e}")
            return {"documents": [], "profile_chunks": []}

    def get_user_data(self, user_id: int) -> Dict:
        """retrieve all data for a user (profile chunks + documents) - UPDATED"""
        if not self.qdrant_client:
            return {"profile_chunks": [], "documents": []}

        try:
            # get all points for this user
            result = self.qdrant_client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
                ),
                with_payload=True,
                with_vectors=False,
                limit=100
            )

            profile_chunks = []
            documents = []

            for point in result[0]:  # result is (points, next_page_offset)
                if point.payload.get("type") == "profile_chunk":
                    profile_chunks.append({
                        'id': point.id,
                        'chunk_type': point.payload.get('chunk_type', ''),
                        'chunk_category': point.payload.get('chunk_category', ''),
                        'data': point.payload
                    })
                elif point.payload.get("type") == "document":
                    documents.append({
                        'id': point.id,
                        'source': point.payload.get('source', ''),
                        'chunk_index': point.payload.get('chunk_index', 0),
                        'data': point.payload
                    })

            # sort documents by chunk_index
            documents.sort(key=lambda x: x['chunk_index'])

            # sort profile chunks by type for consistency
            profile_chunks.sort(key=lambda x: x['chunk_type'])

            logger.info(f"retrieved data for user {user_id}: {len(profile_chunks)} profile chunks, {len(documents)} documents")

            return {
                "profile_chunks": profile_chunks,
                "documents": documents,
                # legacy compatibility
                "profile": profile_chunks[0] if profile_chunks else None
            }

        except Exception as e:
            logger.error(f"failed to get user data for {user_id}: {e}")
            return {"profile_chunks": [], "documents": []}

    def delete_document_embeddings(self, user_id: int, document_id: str) -> bool:
        """delete all embeddings for a specific document"""
        if not self.qdrant_client:
            return False

        try:
            # delete all points for this specific document
            self.qdrant_client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                            FieldCondition(key="type", match=MatchValue(value="document")),
                            FieldCondition(key="document_id", match=MatchValue(value=str(document_id)))
                        ]
                    )
                )
            )

            logger.info(f"deleted embeddings for document {document_id} (user {user_id})")
            return True

        except Exception as e:
            logger.error(f"failed to delete embeddings for document {document_id}: {e}")
            return False

    def delete_user_data(self, user_id: int) -> bool:
        """delete all data for a user"""
        if not self.qdrant_client:
            return False

        try:
            # delete all points for this user
            self.qdrant_client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(
                                key="user_id",
                                match=MatchValue(value=user_id)
                            )
                        ]
                    )
                )
            )

            logger.info(f"deleted all data for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"failed to delete user data for {user_id}: {e}")
            return False

    def _prepare_text(self, text: str) -> str:
        """clean and prepare text for embedding"""
        if not text:
            return ""

        # basic text cleaning
        cleaned = text.strip()
        cleaned = ' '.join(cleaned.split())  # normalize whitespace

        # truncate if too long (rough estimation: 1 token ≈ 0.75 words)
        max_chars = self.max_tokens * 3  # conservative estimate
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars] + "..."
            logger.warning(f"text truncated from {len(text)} to {len(cleaned)} chars")

        return cleaned

    def _get_cache_key(self, text: str, model: str, dimensions: int) -> str:
        """generate cache key for text + model + dimensions"""
        # create hash of text + model + dimensions for cache key
        cache_input = f"{text}:{model}:{dimensions}"
        text_hash = hashlib.md5(cache_input.encode('utf-8')).hexdigest()
        return f"embedding:{model}:{dimensions}:{text_hash}"

    def get_stats(self) -> Dict:
        """get embedding service statistics - UPDATED"""
        stats = {
            'profile_model': self.profile_model,
            'document_model': self.document_model,
            'profile_dimensions': PROFILE_VECTOR_SIZE,
            'document_dimensions': DOCUMENT_VECTOR_SIZE,
            'max_tokens': self.max_tokens,
            'cache_enabled': True,
            'qdrant_connected': self.qdrant_client is not None,
            'collection_name': COLLECTION_NAME,
            'chunking_enabled': True,
            'chunk_types': list(ProfileChunker.CHUNK_TYPES.keys())
        }

        # add collection stats if available
        if self.qdrant_client:
            try:
                collection_info = self.qdrant_client.get_collection(COLLECTION_NAME)
                stats['collection_stats'] = {
                    'points_count': collection_info.points_count,
                    'vectors_count': collection_info.vectors_count,
                    'indexed_vectors_count': collection_info.indexed_vectors_count
                }
            except:
                pass

        return stats


# singleton instance
embedding_service = None

def get_embedding_service():
    global embedding_service
    if embedding_service is None:
        try:
            embedding_service = EmbeddingService()
            print("embedding service initialized with profile chunking support")
        except Exception as e:
            print(f"embedding service failed: {e}")
            return None
    return embedding_service