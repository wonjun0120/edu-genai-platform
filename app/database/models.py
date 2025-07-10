import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = "app/database/education_platform.db"):
        self.db_path = db_path
        self.ensure_db_directory()
        self.init_database()
    
    def ensure_db_directory(self):
        """데이터베이스 디렉토리 생성"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn
    
    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 사용자 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('student', 'instructor', 'admin')),
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # 강의 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL,
                description TEXT,
                instructor_id TEXT NOT NULL,
                semester TEXT NOT NULL,
                credit INTEGER NOT NULL,
                max_students INTEGER NOT NULL,
                department TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (instructor_id) REFERENCES users (id)
            )
        ''')
        
        # 수강신청 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'dropped', 'completed')),
                FOREIGN KEY (student_id) REFERENCES users (id),
                FOREIGN KEY (course_id) REFERENCES courses (id),
                UNIQUE(student_id, course_id)
            )
        ''')
        
        # 문서 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                course_id TEXT NOT NULL,
                uploaded_by TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content_text TEXT,
                is_processed BOOLEAN DEFAULT 0,
                is_vectorized BOOLEAN DEFAULT 0,
                FOREIGN KEY (course_id) REFERENCES courses (id),
                FOREIGN KEY (uploaded_by) REFERENCES users (id)
            )
        ''')
        
        # 벡터 인덱스 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vector_indexes (
                id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                index_path TEXT NOT NULL,
                embedding_model TEXT NOT NULL,
                dimension INTEGER NOT NULL,
                document_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses (id)
            )
        ''')
        
        # 문서 청크 테이블 (벡터 검색용)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_size INTEGER NOT NULL,
                vector_index INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        ''')
        
        # 검색 기록 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                course_id TEXT,
                query TEXT NOT NULL,
                search_type TEXT NOT NULL CHECK (search_type IN ('vector', 'keyword', 'hybrid')),
                results_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (course_id) REFERENCES courses (id)
            )
        ''')
        
        # 인덱스 생성
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_course ON documents(course_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id)')
        
        conn.commit()
        conn.close()
    
    # 사용자 관리
    def create_user(self, name: str, role: str, email: str = None) -> str:
        """사용자 생성"""
        user_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (id, name, role, email, last_login)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, name, role, email, datetime.now()))
        
        conn.commit()
        conn.close()
        return user_id
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """사용자 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def get_user_by_name_role(self, name: str, role: str) -> Optional[Dict]:
        """이름과 역할로 사용자 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE name = ? AND role = ?', (name, role))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    # 강의 관리
    def create_course(self, name: str, code: str, instructor_id: str, semester: str, 
                     credit: int, max_students: int, department: str = None, 
                     description: str = None) -> str:
        """강의 생성"""
        course_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO courses (id, name, code, instructor_id, semester, credit, 
                               max_students, department, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (course_id, name, code, instructor_id, semester, credit, max_students, department, description))
        
        conn.commit()
        conn.close()
        return course_id
    
    def get_courses_by_instructor(self, instructor_id: str) -> List[Dict]:
        """교수자의 강의 목록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, u.name as instructor_name
            FROM courses c
            JOIN users u ON c.instructor_id = u.id
            WHERE c.instructor_id = ? AND c.is_active = 1
            ORDER BY c.created_at DESC
        ''', (instructor_id,))
        
        courses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return courses
    
    def get_inactive_courses_by_instructor(self, instructor_id: str) -> List[Dict]:
        """교수자의 비활성화된 강의 목록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, u.name as instructor_name
            FROM courses c
            JOIN users u ON c.instructor_id = u.id
            WHERE c.instructor_id = ? AND c.is_active = 0
            ORDER BY c.created_at DESC
        ''', (instructor_id,))
        
        courses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return courses
    
    def get_active_courses(self) -> List[Dict]:
        """활성화된 강의 목록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, u.name as instructor_name
            FROM courses c
            JOIN users u ON c.instructor_id = u.id
            WHERE c.is_active = 1
            ORDER BY c.created_at DESC
        ''')
        
        courses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return courses
    
    def update_course_status(self, course_id: str, is_active: bool) -> bool:
        """강의 상태 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE courses 
                SET is_active = ?
                WHERE id = ?
            ''', (is_active, course_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.close()
            return False
    
    def update_course_info(self, course_id: str, **kwargs) -> bool:
        """강의 정보 업데이트"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 업데이트 가능한 필드들
            allowed_fields = [
                'name', 'description', 'semester', 'credit', 'max_students', 
                'department', 'is_active'
            ]
            
            # 업데이트할 필드와 값 추출
            update_fields = []
            update_values = []
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)
            
            if not update_fields:
                return False
            
            # 쿼리 생성
            query = f"UPDATE courses SET {', '.join(update_fields)} WHERE id = ?"
            update_values.append(course_id)
            
            cursor.execute(query, update_values)
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"강의 정보 업데이트 오류: {str(e)}")
            return False
    
    def get_course_by_id(self, course_id: str) -> Optional[Dict]:
        """강의 ID로 강의 정보 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, u.name as instructor_name
            FROM courses c
            JOIN users u ON c.instructor_id = u.id
            WHERE c.id = ?
        ''', (course_id,))
        
        course = cursor.fetchone()
        conn.close()
        
        return dict(course) if course else None
    
    # 수강신청 관리
    def enroll_student(self, student_id: str, course_id: str) -> bool:
        """학생 수강신청"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            enrollment_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO enrollments (id, student_id, course_id)
                VALUES (?, ?, ?)
            ''', (enrollment_id, student_id, course_id))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False  # 이미 수강신청한 경우
    
    def get_student_courses(self, student_id: str) -> List[Dict]:
        """학생의 수강 강의 목록"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, u.name as instructor_name, e.enrolled_at, e.status
            FROM courses c
            JOIN enrollments e ON c.id = e.course_id
            JOIN users u ON c.instructor_id = u.id
            WHERE e.student_id = ? AND e.status = 'active'
            ORDER BY e.enrolled_at DESC
        ''', (student_id,))
        
        courses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return courses
    
    def get_course_enrollments(self, course_id: str) -> List[Dict]:
        """강의 수강생 목록"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.*, e.enrolled_at, e.status
            FROM users u
            JOIN enrollments e ON u.id = e.student_id
            WHERE e.course_id = ? AND e.status = 'active'
            ORDER BY e.enrolled_at DESC
        ''', (course_id,))
        
        students = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return students
    
    # 문서 관리
    def create_document(self, filename: str, original_filename: str, file_path: str,
                       file_type: str, file_size: int, course_id: str, uploaded_by: str) -> str:
        """문서 생성"""
        doc_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO documents (id, filename, original_filename, file_path, file_type, 
                                 file_size, course_id, uploaded_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (doc_id, filename, original_filename, file_path, file_type, file_size, course_id, uploaded_by))
        
        conn.commit()
        conn.close()
        return doc_id
    
    def get_course_documents(self, course_id: str) -> List[Dict]:
        """강의 문서 목록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT d.*, 
                   COALESCE(u.name, d.uploaded_by) as uploader_name
            FROM documents d
            LEFT JOIN users u ON d.uploaded_by = u.id
            WHERE d.course_id = ?
            ORDER BY d.uploaded_at DESC
        ''', (course_id,))
        
        documents = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return documents
    
    def update_document_content(self, doc_id: str, content_text: str):
        """문서 내용 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE documents 
            SET content_text = ?, is_processed = 1
            WHERE id = ?
        ''', (content_text, doc_id))
        
        conn.commit()
        conn.close()
    
    def mark_document_vectorized(self, doc_id: str):
        """문서 벡터화 완료 표시"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE documents 
            SET is_vectorized = 1
            WHERE id = ?
        ''', (doc_id,))
        
        conn.commit()
        conn.close()
    
    def delete_document(self, doc_id: str) -> bool:
        """문서 삭제"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 먼저 관련 청크들 삭제
            cursor.execute('DELETE FROM document_chunks WHERE document_id = ?', (doc_id,))
            
            # 문서 삭제
            cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"문서 삭제 중 오류: {str(e)}")
            return False
    
    # 벡터 인덱스 관리
    def create_vector_index(self, course_id: str, index_path: str, embedding_model: str, dimension: int) -> str:
        """벡터 인덱스 생성"""
        index_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vector_indexes (id, course_id, index_path, embedding_model, dimension)
            VALUES (?, ?, ?, ?, ?)
        ''', (index_id, course_id, index_path, embedding_model, dimension))
        
        conn.commit()
        conn.close()
        return index_id
    
    def get_vector_index(self, course_id: str) -> Optional[Dict]:
        """강의의 벡터 인덱스 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM vector_indexes WHERE course_id = ?
        ''', (course_id,))
        
        index = cursor.fetchone()
        conn.close()
        
        return dict(index) if index else None
    
    def update_vector_index_stats(self, index_id: str, document_count: int):
        """벡터 인덱스 통계 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE vector_indexes 
            SET document_count = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (document_count, index_id))
        
        conn.commit()
        conn.close()
    
    # 문서 청크 관리
    def create_document_chunk(self, document_id: str, chunk_index: int, chunk_text: str, vector_index: int = None) -> str:
        """문서 청크 생성"""
        chunk_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO document_chunks (id, document_id, chunk_index, chunk_text, chunk_size, vector_index)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (chunk_id, document_id, chunk_index, chunk_text, len(chunk_text), vector_index))
        
        conn.commit()
        conn.close()
        return chunk_id
    
    def get_document_chunks(self, document_id: str) -> List[Dict]:
        """문서 청크 목록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM document_chunks WHERE document_id = ? ORDER BY chunk_index
        ''', (document_id,))
        
        chunks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return chunks
    
    # 검색 기록 관리
    def log_search(self, user_id: str, query: str, search_type: str, results_count: int, course_id: str = None):
        """검색 기록 저장"""
        search_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_history (id, user_id, course_id, query, search_type, results_count)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (search_id, user_id, course_id, query, search_type, results_count))
        
        conn.commit()
        conn.close()
    
    def get_user_search_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """사용자 검색 기록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, c.name as course_name
            FROM search_history s
            LEFT JOIN courses c ON s.course_id = c.id
            WHERE s.user_id = ?
            ORDER BY s.created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return history 