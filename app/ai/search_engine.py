import logging
from typing import Dict, List, Optional, Tuple
import asyncio
import time
from datetime import datetime

from database.models import DatabaseManager
from vector.faiss_manager import FAISSVectorManager
from processing.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class AISearchEngine:
    """AI 기반 검색 엔진"""
    
    def __init__(self, db_manager: DatabaseManager = None, vector_manager: FAISSVectorManager = None):
        """
        초기화
        Args:
            db_manager: 데이터베이스 매니저
            vector_manager: 벡터 매니저
        """
        self.db_manager = db_manager or DatabaseManager()
        self.vector_manager = vector_manager or FAISSVectorManager()
        self.document_processor = DocumentProcessor()
        
        logger.info("AI 검색 엔진 초기화 완료")
    
    async def index_course_documents(self, course_id: str, force_reindex: bool = False) -> Dict:
        """
        강의 문서들을 인덱싱
        Args:
            course_id: 강의 ID
            force_reindex: 강제 재인덱싱 여부
        Returns:
            인덱싱 결과
        """
        try:
            start_time = time.time()
            
            # 강의 문서 목록 조회
            documents = self.db_manager.get_course_documents(course_id)
            
            if not documents:
                return {
                    'success': False,
                    'message': '인덱싱할 문서가 없습니다.',
                    'processed_count': 0,
                    'total_count': 0
                }
            
            # 처리할 문서 필터링
            documents_to_process = []
            processed_count = 0
            error_count = 0
            
            for doc in documents:
                # 이미 처리되었고 강제 재인덱싱이 아닌 경우 스킵
                if doc['is_vectorized'] and not force_reindex:
                    continue
                
                # 파일 존재 여부 확인
                if not self.document_processor.is_supported_format(doc['file_path']):
                    logger.warning(f"지원되지 않는 파일 형식: {doc['file_path']}")
                    continue
                
                # 텍스트 추출
                extraction_result = self.document_processor.extract_text_from_file(doc['file_path'])
                
                if extraction_result['success'] and extraction_result['text']:
                    # 문서 내용 DB에 저장
                    self.db_manager.update_document_content(doc['id'], extraction_result['text'])
                    
                    documents_to_process.append({
                        'id': doc['id'],
                        'text': extraction_result['text'],
                        'metadata': {
                            'filename': doc['filename'],
                            'file_type': doc['file_type'],
                            'uploaded_at': doc['uploaded_at'],
                            'uploader': doc['uploader_name'],
                            'page_count': extraction_result.get('page_count', 0),
                            'word_count': extraction_result.get('word_count', 0)
                        }
                    })
                    processed_count += 1
                else:
                    error_count += 1
                    logger.error(f"텍스트 추출 실패: {doc['filename']} - {extraction_result.get('error', '알 수 없는 오류')}")
            
            # 벡터 인덱싱
            if documents_to_process:
                chunk_count = self.vector_manager.add_documents_to_index(course_id, documents_to_process)
                
                # 문서 벡터화 완료 표시
                for doc in documents_to_process:
                    self.db_manager.mark_document_vectorized(doc['id'])
                
                logger.info(f"인덱싱 완료: {course_id}, 문서 수: {processed_count}, 청크 수: {chunk_count}")
            
            end_time = time.time()
            
            return {
                'success': True,
                'message': f'인덱싱 완료 - 처리된 문서: {processed_count}개, 전체 문서: {len(documents)}개',
                'processed_count': processed_count,
                'total_count': len(documents),
                'error_count': error_count,
                'processing_time': end_time - start_time,
                'chunk_count': chunk_count if documents_to_process else 0
            }
            
        except Exception as e:
            logger.error(f"인덱싱 중 오류 발생: {str(e)}")
            return {
                'success': False,
                'message': f'인덱싱 중 오류가 발생했습니다: {str(e)}',
                'processed_count': 0,
                'total_count': 0,
                'error_count': 1
            }
    
    def search_documents(self, course_id: str, query: str, user_id: str = None, 
                        search_type: str = 'vector', top_k: int = 5,
                        min_similarity: float = 0.5) -> Dict:
        """
        문서 검색
        Args:
            course_id: 강의 ID
            query: 검색 쿼리
            user_id: 사용자 ID (검색 로그용)
            search_type: 검색 타입 ('vector', 'keyword', 'hybrid')
            top_k: 반환할 결과 수
            min_similarity: 최소 유사도 점수
        Returns:
            검색 결과
        """
        try:
            start_time = time.time()
            
            if search_type == 'vector':
                results = self._vector_search(course_id, query, top_k, min_similarity)
            elif search_type == 'keyword':
                results = self._keyword_search(course_id, query, top_k)
            elif search_type == 'hybrid':
                results = self._hybrid_search(course_id, query, top_k, min_similarity)
            else:
                raise ValueError(f"지원되지 않는 검색 타입: {search_type}")
            
            # 검색 로그 저장
            if user_id:
                self.db_manager.log_search(user_id, query, search_type, len(results), course_id)
            
            end_time = time.time()
            
            return {
                'success': True,
                'query': query,
                'search_type': search_type,
                'results': results,
                'result_count': len(results),
                'search_time': end_time - start_time
            }
            
        except Exception as e:
            logger.error(f"검색 중 오류 발생: {str(e)}")
            return {
                'success': False,
                'query': query,
                'search_type': search_type,
                'results': [],
                'result_count': 0,
                'error': str(e)
            }
    
    def _vector_search(self, course_id: str, query: str, top_k: int, min_similarity: float) -> List[Dict]:
        """벡터 기반 검색"""
        try:
            # FAISS 벡터 검색
            vector_results = self.vector_manager.search_course_documents(
                course_id, query, top_k, min_similarity
            )
            
            # 문서 메타데이터 추가
            enriched_results = []
            for result in vector_results:
                doc_id = result['document_id']
                
                # 데이터베이스에서 문서 정보 조회
                documents = self.db_manager.get_course_documents(course_id)
                doc_info = next((doc for doc in documents if doc['id'] == doc_id), None)
                
                if doc_info:
                    enriched_results.append({
                        'document_id': doc_id,
                        'filename': doc_info['filename'],
                        'file_type': doc_info['file_type'],
                        'uploaded_at': doc_info['uploaded_at'],
                        'uploader': doc_info['uploader_name'],
                        'similarity': result['similarity'],
                        'chunk_index': result['chunk_index'],
                        'text_preview': result['text'],
                        'content': result['text'],  # 채팅 서비스에서 사용할 content 필드 추가
                        'search_type': 'vector'
                    })
            
            return enriched_results
            
        except Exception as e:
            logger.error(f"벡터 검색 중 오류: {str(e)}")
            return []
    
    def _keyword_search(self, course_id: str, query: str, top_k: int) -> List[Dict]:
        """키워드 기반 검색"""
        try:
            # 강의 문서 목록 조회
            documents = self.db_manager.get_course_documents(course_id)
            
            results = []
            query_lower = query.lower()
            
            for doc in documents:
                if not doc['content_text']:
                    continue
                
                content_lower = doc['content_text'].lower()
                
                # 키워드 매칭
                if query_lower in content_lower:
                    # 키워드 주변 텍스트 추출
                    start_idx = content_lower.find(query_lower)
                    start_preview = max(0, start_idx - 100)
                    end_preview = min(len(doc['content_text']), start_idx + len(query) + 100)
                    
                    preview_text = doc['content_text'][start_preview:end_preview]
                    
                    # 키워드 빈도 계산
                    keyword_count = content_lower.count(query_lower)
                    
                    results.append({
                        'document_id': doc['id'],
                        'filename': doc['filename'],
                        'file_type': doc['file_type'],
                        'uploaded_at': doc['uploaded_at'],
                        'uploader': doc['uploader_name'],
                        'keyword_count': keyword_count,
                        'text_preview': preview_text,
                        'content': preview_text,  # 채팅 서비스에서 사용할 content 필드 추가
                        'search_type': 'keyword'
                    })
            
            # 키워드 빈도순으로 정렬
            results.sort(key=lambda x: x['keyword_count'], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"키워드 검색 중 오류: {str(e)}")
            return []
    
    def _hybrid_search(self, course_id: str, query: str, top_k: int, min_similarity: float) -> List[Dict]:
        """하이브리드 검색 (벡터 + 키워드)"""
        try:
            # 벡터 검색 결과
            vector_results = self._vector_search(course_id, query, top_k, min_similarity)
            
            # 키워드 검색 결과
            keyword_results = self._keyword_search(course_id, query, top_k)
            
            # 결과 병합 및 중복 제거
            combined_results = {}
            
            # 벡터 검색 결과 추가 (높은 가중치)
            for result in vector_results:
                doc_id = result['document_id']
                score = result['similarity'] * 0.7  # 벡터 검색 가중치 70%
                
                combined_results[doc_id] = {
                    **result,
                    'hybrid_score': score,
                    'search_type': 'hybrid'
                }
            
            # 키워드 검색 결과 추가
            for result in keyword_results:
                doc_id = result['document_id']
                # 키워드 점수 정규화 (0~1 범위)
                keyword_score = min(result['keyword_count'] / 10, 1.0) * 0.3  # 키워드 검색 가중치 30%
                
                if doc_id in combined_results:
                    # 이미 벡터 검색 결과에 있는 경우 점수 합산
                    combined_results[doc_id]['hybrid_score'] += keyword_score
                    combined_results[doc_id]['keyword_count'] = result['keyword_count']
                else:
                    # 키워드 검색에서만 발견된 경우
                    combined_results[doc_id] = {
                        **result,
                        'hybrid_score': keyword_score,
                        'search_type': 'hybrid'
                    }
                    # content 필드가 없는 경우 text_preview로 대체
                    if 'content' not in combined_results[doc_id]:
                        combined_results[doc_id]['content'] = result.get('text_preview', '')
            
            # 하이브리드 점수순으로 정렬
            sorted_results = sorted(
                combined_results.values(),
                key=lambda x: x['hybrid_score'],
                reverse=True
            )
            
            return sorted_results[:top_k]
            
        except Exception as e:
            logger.error(f"하이브리드 검색 중 오류: {str(e)}")
            return []
    
    def get_search_suggestions(self, course_id: str, query: str, limit: int = 5) -> List[str]:
        """검색 제안어 생성"""
        try:
            # 강의 문서의 주요 키워드 추출
            documents = self.db_manager.get_course_documents(course_id)
            
            suggestions = []
            query_lower = query.lower()
            
            for doc in documents:
                if not doc['content_text']:
                    continue
                
                # 간단한 키워드 추출 (추후 개선 가능)
                words = doc['content_text'].lower().split()
                
                for word in words:
                    if (len(word) > 2 and 
                        query_lower in word and 
                        word not in suggestions and
                        word != query_lower):
                        suggestions.append(word)
                        
                        if len(suggestions) >= limit:
                            break
                
                if len(suggestions) >= limit:
                    break
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"검색 제안어 생성 중 오류: {str(e)}")
            return []
    
    def get_course_search_stats(self, course_id: str) -> Dict:
        """강의별 검색 통계"""
        try:
            # 벡터 인덱스 통계
            vector_stats = self.vector_manager.get_course_index_stats(course_id)
            
            # 문서 통계
            documents = self.db_manager.get_course_documents(course_id)
            processed_docs = len([doc for doc in documents if doc['is_processed']])
            vectorized_docs = len([doc for doc in documents if doc['is_vectorized']])
            
            return {
                'total_documents': len(documents),
                'processed_documents': processed_docs,
                'vectorized_documents': vectorized_docs,
                'vector_stats': vector_stats,
                'processing_rate': (processed_docs / len(documents) * 100) if documents else 0,
                'vectorization_rate': (vectorized_docs / len(documents) * 100) if documents else 0
            }
            
        except Exception as e:
            logger.error(f"검색 통계 조회 중 오류: {str(e)}")
            return {
                'total_documents': 0,
                'processed_documents': 0,
                'vectorized_documents': 0,
                'vector_stats': {},
                'processing_rate': 0,
                'vectorization_rate': 0
            }
    
    def get_user_search_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """사용자 검색 기록"""
        try:
            return self.db_manager.get_user_search_history(user_id, limit)
        except Exception as e:
            logger.error(f"검색 기록 조회 중 오류: {str(e)}")
            return [] 