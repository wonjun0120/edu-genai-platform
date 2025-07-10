import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

# 현재 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from database.models import DatabaseManager
from processing.document_processor import DocumentProcessor  
from vector.faiss_manager import FAISSVectorManager
from integration.bridge import SystemBridge

logger = logging.getLogger(__name__)

class DocumentService:
    """문서 업로드, 처리, 벡터화까지 전체 워크플로우 관리 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.db_manager = DatabaseManager()
        self.doc_processor = DocumentProcessor()
        self.vector_manager = FAISSVectorManager()
        self.system_bridge = SystemBridge()
        
        logger.info("문서 서비스 초기화 완료")
    
    def process_uploaded_file(self, uploaded_file, course_id: str, user_id: str) -> Dict:
        """
        업로드된 파일 전체 처리 워크플로우
        Args:
            uploaded_file: Streamlit 업로드 파일 객체
            course_id: 강의 ID
            user_id: 업로드 사용자 ID
        Returns:
            처리 결과 딕셔너리
        """
        try:
            logger.info(f"파일 처리 시작: {uploaded_file.name}")
            
            # Phase 1: 파일 저장
            file_path, metadata = self.doc_processor.save_uploaded_file(
                uploaded_file, course_id, user_id
            )
            
            # Phase 2: 텍스트 추출
            extraction_result = self.doc_processor.extract_text_from_file(file_path)
            
            if not extraction_result['success']:
                return {
                    'success': False,
                    'error': f"텍스트 추출 실패: {extraction_result['error']}",
                    'file_path': file_path
                }
            
            # Phase 3: 데이터베이스에 문서 정보 저장
            doc_id = self.db_manager.create_document(
                filename=metadata['saved_filename'],
                original_filename=metadata['original_filename'],
                file_path=file_path,
                file_type=metadata['file_type'],
                file_size=metadata['file_size'],
                course_id=course_id,
                uploaded_by=user_id
            )
            
            # Phase 4: 텍스트 내용 업데이트
            self.db_manager.update_document_content(doc_id, extraction_result['text'])
            
            # Phase 5: 벡터화 및 인덱스 추가
            vectorization_result = self._vectorize_document(
                doc_id, extraction_result['text'], course_id
            )
            
            if vectorization_result['success']:
                # 벡터화 완료 표시
                self.db_manager.mark_document_vectorized(doc_id)
                
                # 벡터 인덱스 정보 업데이트
                self._update_vector_index_info(course_id)
            
            return {
                'success': True,
                'document_id': doc_id,
                'file_path': file_path,
                'text_length': len(extraction_result['text']),
                'word_count': extraction_result['word_count'],
                'page_count': extraction_result['page_count'],
                'vectorized': vectorization_result['success'],
                'chunk_count': vectorization_result.get('chunk_count', 0),
                'message': f"'{uploaded_file.name}' 파일 처리 완료"
            }
            
        except Exception as e:
            logger.error(f"파일 처리 중 오류 발생: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path if 'file_path' in locals() else None
            }
    
    def _vectorize_document(self, doc_id: str, text: str, course_id: str) -> Dict:
        """
        문서 벡터화 처리
        Args:
            doc_id: 문서 ID
            text: 문서 텍스트
            course_id: 강의 ID
        Returns:
            벡터화 결과
        """
        try:
            # 문서 리스트 형태로 변환
            documents = [{
                'id': doc_id,
                'text': text,
                'metadata': {'course_id': course_id}
            }]
            
            # FAISS 인덱스에 추가
            chunk_count = self.vector_manager.add_documents_to_index(course_id, documents)
            
            # 생성된 청크들을 데이터베이스에 저장
            self._save_document_chunks(doc_id, text)
            
            logger.info(f"문서 벡터화 완료: {doc_id}, 청크 수: {chunk_count}")
            
            return {
                'success': True,
                'chunk_count': chunk_count,
                'message': '벡터화 완료'
            }
            
        except Exception as e:
            logger.error(f"벡터화 중 오류 발생: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chunk_count': 0
            }
    
    def _save_document_chunks(self, doc_id: str, text: str, chunk_size: int = 1000):
        """
        문서 청크를 데이터베이스에 저장
        Args:
            doc_id: 문서 ID
            text: 전체 텍스트
            chunk_size: 청크 크기
        """
        try:
            # 텍스트를 청크로 분할
            chunks = self._split_text_into_chunks(text, chunk_size)
            
            # 데이터베이스에 청크 저장
            for i, chunk in enumerate(chunks):
                self.db_manager.create_document_chunk(
                    document_id=doc_id,
                    chunk_index=i,
                    chunk_text=chunk,
                    vector_index=i
                )
            
            logger.info(f"문서 청크 저장 완료: {doc_id}, 청크 수: {len(chunks)}")
            
        except Exception as e:
            logger.error(f"청크 저장 중 오류 발생: {str(e)}")
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """
        텍스트를 청크로 분할
        Args:
            text: 분할할 텍스트
            chunk_size: 청크 크기
        Returns:
            청크 리스트
        """
        if not text:
            return []
        
        chunks = []
        sentences = text.split('. ')
        
        current_chunk = ""
        for sentence in sentences:
            test_chunk = current_chunk + ". " + sentence if current_chunk else sentence
            
            if len(test_chunk) <= chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [chunk for chunk in chunks if len(chunk) > 50]
    
    def _update_vector_index_info(self, course_id: str):
        """
        벡터 인덱스 정보 업데이트
        Args:
            course_id: 강의 ID
        """
        try:
            # 기존 벡터 인덱스 정보 조회
            existing_index = self.db_manager.get_vector_index(course_id)
            
            if not existing_index:
                # 새로운 벡터 인덱스 정보 생성
                index_path = f"app/vector/data/course_{course_id}.faiss"
                self.db_manager.create_vector_index(
                    course_id=course_id,
                    index_path=index_path,
                    embedding_model=self.vector_manager.embedding_model_name,
                    dimension=self.vector_manager.dimension
                )
            
            # 벡터 인덱스 통계 업데이트
            stats = self.vector_manager.get_course_index_stats(course_id)
            if existing_index:
                self.db_manager.update_vector_index_stats(
                    existing_index['id'], 
                    stats['document_count']
                )
            
        except Exception as e:
            logger.error(f"벡터 인덱스 정보 업데이트 중 오류: {str(e)}")
    
    def search_course_documents(self, course_id: str, query: str, user_id: str, 
                               top_k: int = 5, search_type: str = "vector") -> Dict:
        """
        강의 문서 검색
        Args:
            course_id: 강의 ID
            query: 검색 쿼리
            user_id: 검색 사용자 ID
            top_k: 반환할 결과 수
            search_type: 검색 타입 (vector, keyword, hybrid)
        Returns:
            검색 결과
        """
        try:
            # 벡터 검색 수행
            if search_type in ["vector", "hybrid"]:
                results = self.vector_manager.search_course_documents(
                    course_id=course_id,
                    query=query,
                    top_k=top_k,
                    min_similarity=0.3
                )
            else:
                # 키워드 검색 (추후 구현)
                results = []
            
            # 검색 로그 저장
            self.db_manager.log_search(
                user_id=user_id,
                query=query,
                search_type=search_type,
                results_count=len(results),
                course_id=course_id
            )
            
            return {
                'success': True,
                'results': results,
                'total_count': len(results),
                'query': query,
                'search_type': search_type
            }
            
        except Exception as e:
            logger.error(f"검색 중 오류 발생: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'results': [],
                'total_count': 0
            }
    
    def get_course_document_stats(self, course_id: str) -> Dict:
        """
        강의 문서 통계 조회
        Args:
            course_id: 강의 ID
        Returns:
            문서 통계 정보
        """
        try:
            # 데이터베이스 문서 통계
            documents = self.db_manager.get_course_documents(course_id)
            
            # 벡터 인덱스 통계
            vector_stats = self.vector_manager.get_course_index_stats(course_id)
            
            return {
                'total_documents': len(documents),
                'vectorized_documents': len([d for d in documents if d['is_vectorized']]),
                'total_file_size': sum(d['file_size'] for d in documents),
                'vector_index_size_mb': vector_stats['index_size_mb'],
                'total_chunks': vector_stats['chunk_count'],
                'embedding_model': vector_stats['embedding_model'],
                'vector_dimension': vector_stats['dimension']
            }
            
        except Exception as e:
            logger.error(f"통계 조회 중 오류: {str(e)}")
            return {
                'total_documents': 0,
                'vectorized_documents': 0,
                'total_file_size': 0,
                'vector_index_size_mb': 0,
                'total_chunks': 0,
                'embedding_model': '',
                'vector_dimension': 0
            }
    
    async def batch_process_documents(self, course_id: str, uploaded_files: List, user_id: str) -> List[Dict]:
        """
        여러 문서 일괄 처리 (비동기)
        Args:
            course_id: 강의 ID
            uploaded_files: 업로드된 파일 리스트
            user_id: 사용자 ID
        Returns:
            처리 결과 리스트
        """
        results = []
        
        for uploaded_file in uploaded_files:
            try:
                result = self.process_uploaded_file(uploaded_file, course_id, user_id)
                results.append(result)
                
                # 처리 간 잠시 대기 (시스템 부하 방지)
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"파일 {uploaded_file.name} 처리 중 오류: {str(e)}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'filename': uploaded_file.name
                })
        
        return results 