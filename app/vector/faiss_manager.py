import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Optional
import pickle
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FAISSVectorManager:
    """FAISS 벡터 데이터베이스 관리 클래스"""
    
    def __init__(self, embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        초기화
        Args:
            embedding_model: 사용할 임베딩 모델명
        """
        self.embedding_model_name = embedding_model
        self.embedding_model = SentenceTransformer(embedding_model)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # 벡터 인덱스 저장소
        self.vector_indexes = {}
        self.course_metadata = {}
        
        # 데이터 저장 경로
        self.base_path = Path("app/vector/data")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FAISS Manager 초기화 완료 - 모델: {embedding_model}, 차원: {self.dimension}")
    
    def create_course_index(self, course_id: str, force_recreate: bool = False) -> str:
        """
        강의별 벡터 인덱스 생성
        Args:
            course_id: 강의 ID
            force_recreate: 기존 인덱스 강제 재생성 여부
        Returns:
            인덱스 파일 경로
        """
        index_path = self.base_path / f"course_{course_id}.faiss"
        metadata_path = self.base_path / f"course_{course_id}_metadata.pkl"
        
        if index_path.exists() and not force_recreate:
            logger.info(f"기존 인덱스 로드: {index_path}")
            return str(index_path)
        
        # 새로운 FAISS 인덱스 생성
        index = faiss.IndexFlatIP(self.dimension)  # 내적 기반 유사도 검색
        
        # 인덱스 저장
        faiss.write_index(index, str(index_path))
        
        # 메타데이터 초기화
        metadata = {
            'course_id': course_id,
            'embedding_model': self.embedding_model_name,
            'dimension': self.dimension,
            'document_count': 0,
            'chunk_count': 0,
            'chunk_metadata': []
        }
        
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"새로운 인덱스 생성 완료: {index_path}")
        return str(index_path)
    
    def load_course_index(self, course_id: str) -> Tuple[faiss.Index, Dict]:
        """
        강의 인덱스 로드
        Args:
            course_id: 강의 ID
        Returns:
            FAISS 인덱스와 메타데이터
        """
        index_path = self.base_path / f"course_{course_id}.faiss"
        metadata_path = self.base_path / f"course_{course_id}_metadata.pkl"
        
        if not index_path.exists():
            raise FileNotFoundError(f"인덱스 파일이 없습니다: {index_path}")
        
        # 인덱스 로드
        index = faiss.read_index(str(index_path))
        
        # 메타데이터 로드
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        return index, metadata
    
    def save_course_index(self, course_id: str, index: faiss.Index, metadata: Dict):
        """
        강의 인덱스 저장
        Args:
            course_id: 강의 ID
            index: FAISS 인덱스
            metadata: 메타데이터
        """
        index_path = self.base_path / f"course_{course_id}.faiss"
        metadata_path = self.base_path / f"course_{course_id}_metadata.pkl"
        
        faiss.write_index(index, str(index_path))
        
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"인덱스 저장 완료: {index_path}")
    
    def add_documents_to_index(self, course_id: str, documents: List[Dict]) -> int:
        """
        문서들을 인덱스에 추가
        Args:
            course_id: 강의 ID
            documents: 문서 리스트 [{'id': str, 'text': str, 'metadata': dict}]
        Returns:
            추가된 청크 수
        """
        try:
            # 인덱스 로드 (없으면 생성)
            try:
                index, metadata = self.load_course_index(course_id)
            except FileNotFoundError:
                self.create_course_index(course_id)
                index, metadata = self.load_course_index(course_id)
            
            # 문서 청크 생성 및 임베딩
            all_chunks = []
            chunk_metadata = metadata.get('chunk_metadata', [])
            
            for doc in documents:
                doc_chunks = self._split_document(doc['text'], doc['id'])
                all_chunks.extend(doc_chunks)
                
                # 메타데이터 업데이트
                for chunk in doc_chunks:
                    chunk_metadata.append({
                        'document_id': doc['id'],
                        'chunk_index': chunk['chunk_index'],
                        'text': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text'],
                        'original_metadata': doc.get('metadata', {})
                    })
            
            if not all_chunks:
                logger.warning(f"추가할 청크가 없습니다: {course_id}")
                return 0
            
            # 텍스트 임베딩 생성
            texts = [chunk['text'] for chunk in all_chunks]
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            
            # 임베딩 정규화 (내적 검색을 위해)
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # 인덱스에 벡터 추가
            index.add(embeddings.astype(np.float32))
            
            # 메타데이터 업데이트
            metadata['document_count'] = len(set(doc['id'] for doc in documents))
            metadata['chunk_count'] = index.ntotal
            metadata['chunk_metadata'] = chunk_metadata
            
            # 인덱스 저장
            self.save_course_index(course_id, index, metadata)
            
            logger.info(f"문서 추가 완료: {course_id}, 청크 수: {len(all_chunks)}")
            return len(all_chunks)
            
        except Exception as e:
            logger.error(f"문서 추가 중 오류 발생: {str(e)}")
            raise
    
    def search_course_documents(self, course_id: str, query: str, top_k: int = 5, 
                               min_similarity: float = 0.5) -> List[Dict]:
        """
        강의 문서에서 유사도 검색
        Args:
            course_id: 강의 ID
            query: 검색 쿼리
            top_k: 반환할 결과 수
            min_similarity: 최소 유사도 점수
        Returns:
            검색 결과 리스트
        """
        try:
            # 인덱스 로드
            index, metadata = self.load_course_index(course_id)
            
            if index.ntotal == 0:
                logger.warning(f"빈 인덱스: {course_id}")
                return []
            
            # 쿼리 임베딩 생성
            query_embedding = self.embedding_model.encode([query], convert_to_tensor=False)
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
            
            # 유사도 검색
            similarities, indices = index.search(query_embedding.astype(np.float32), top_k)
            
            # 결과 구성
            results = []
            chunk_metadata = metadata.get('chunk_metadata', [])
            
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                if similarity < min_similarity:
                    continue
                
                if idx < len(chunk_metadata):
                    chunk_info = chunk_metadata[idx]
                    results.append({
                        'rank': i + 1,
                        'similarity': float(similarity),
                        'document_id': chunk_info['document_id'],
                        'chunk_index': chunk_info['chunk_index'],
                        'text': chunk_info['text'],
                        'metadata': chunk_info.get('original_metadata', {})
                    })
            
            logger.info(f"검색 완료: {course_id}, 쿼리: {query}, 결과 수: {len(results)}")
            return results
            
        except FileNotFoundError:
            logger.warning(f"인덱스가 없습니다: {course_id}")
            return []
        except Exception as e:
            logger.error(f"검색 중 오류 발생: {str(e)}")
            raise
    
    def _split_document(self, text: str, document_id: str, chunk_size: int = 1000, 
                       chunk_overlap: int = 200) -> List[Dict]:
        """
        문서를 청크로 분할
        Args:
            text: 문서 텍스트
            document_id: 문서 ID
            chunk_size: 청크 크기
            chunk_overlap: 청크 겹침 크기
        Returns:
            청크 리스트
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        text = text.strip()
        
        # 문장 단위로 분할 시도
        sentences = text.split('. ')
        
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 현재 청크에 문장 추가 시 크기 확인
            test_chunk = current_chunk + ". " + sentence if current_chunk else sentence
            
            if len(test_chunk) <= chunk_size:
                current_chunk = test_chunk
            else:
                # 현재 청크 저장
                if current_chunk:
                    chunks.append({
                        'document_id': document_id,
                        'chunk_index': chunk_index,
                        'text': current_chunk,
                        'size': len(current_chunk)
                    })
                    chunk_index += 1
                
                # 새로운 청크 시작
                current_chunk = sentence
        
        # 마지막 청크 저장
        if current_chunk:
            chunks.append({
                'document_id': document_id,
                'chunk_index': chunk_index,
                'text': current_chunk,
                'size': len(current_chunk)
            })
        
        # 너무 짧은 청크는 제거
        chunks = [chunk for chunk in chunks if len(chunk['text']) > 50]
        
        return chunks
    
    def get_course_index_stats(self, course_id: str) -> Dict:
        """
        강의 인덱스 통계 조회
        Args:
            course_id: 강의 ID
        Returns:
            인덱스 통계 정보
        """
        try:
            index, metadata = self.load_course_index(course_id)
            
            return {
                'course_id': course_id,
                'embedding_model': metadata.get('embedding_model', ''),
                'dimension': metadata.get('dimension', 0),
                'document_count': metadata.get('document_count', 0),
                'chunk_count': index.ntotal,
                'index_size_mb': os.path.getsize(self.base_path / f"course_{course_id}.faiss") / (1024 * 1024),
                'metadata_size_mb': os.path.getsize(self.base_path / f"course_{course_id}_metadata.pkl") / (1024 * 1024)
            }
        except FileNotFoundError:
            return {
                'course_id': course_id,
                'embedding_model': '',
                'dimension': 0,
                'document_count': 0,
                'chunk_count': 0,
                'index_size_mb': 0,
                'metadata_size_mb': 0
            }
    
    def delete_course_index(self, course_id: str) -> bool:
        """
        강의 인덱스 삭제
        Args:
            course_id: 강의 ID
        Returns:
            삭제 성공 여부
        """
        try:
            index_path = self.base_path / f"course_{course_id}.faiss"
            metadata_path = self.base_path / f"course_{course_id}_metadata.pkl"
            
            deleted = False
            
            if index_path.exists():
                os.remove(index_path)
                deleted = True
            
            if metadata_path.exists():
                os.remove(metadata_path)
                deleted = True
            
            if deleted:
                logger.info(f"인덱스 삭제 완료: {course_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"인덱스 삭제 중 오류 발생: {str(e)}")
            return False
    
    def rebuild_course_index(self, course_id: str, documents: List[Dict]) -> bool:
        """
        강의 인덱스 재구축
        Args:
            course_id: 강의 ID
            documents: 문서 리스트
        Returns:
            재구축 성공 여부
        """
        try:
            # 기존 인덱스 삭제
            self.delete_course_index(course_id)
            
            # 새 인덱스 생성
            self.create_course_index(course_id)
            
            # 문서 추가
            chunk_count = self.add_documents_to_index(course_id, documents)
            
            logger.info(f"인덱스 재구축 완료: {course_id}, 청크 수: {chunk_count}")
            return True
            
        except Exception as e:
            logger.error(f"인덱스 재구축 중 오류 발생: {str(e)}")
            return False 