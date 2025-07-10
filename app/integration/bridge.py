import streamlit as st
import uuid
from typing import Dict, List, Optional
from datetime import datetime
import logging
import sys
from pathlib import Path

# 현재 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from database.models import DatabaseManager
from processing.document_processor import DocumentProcessor
from utils.session_utils import get_user_name, get_user_role

logger = logging.getLogger(__name__)

class SystemBridge:
    """세션 기반 시스템과 데이터베이스 시스템을 연결하는 브릿지"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.document_processor = DocumentProcessor()
        logger.info("시스템 브릿지 초기화 완료")
    
    def sync_session_to_database(self):
        """세션 데이터를 데이터베이스로 동기화"""
        try:
            # 현재 사용자 정보 동기화
            user_name = get_user_name()
            user_role = get_user_role()
            
            if user_name and user_role:
                user_id = self.ensure_user_exists(user_name, user_role)
                
                # 강의 정보 동기화
                if user_role == "instructor":
                    self.sync_instructor_courses(user_id)
                elif user_role == "student":
                    self.sync_student_enrollments(user_id)
                
                # 문서 정보 동기화
                self.sync_course_materials()
                
                logger.info(f"세션 동기화 완료: {user_name} ({user_role})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"세션 동기화 중 오류 발생: {str(e)}")
            return False
    
    def ensure_user_exists(self, user_name: str, user_role: str) -> str:
        """사용자 존재 확인 및 생성"""
        try:
            # 기존 사용자 조회
            existing_user = self.db_manager.get_user_by_name_role(user_name, user_role)
            
            if existing_user:
                # 마지막 로그인 시간 업데이트
                conn = self.db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET last_login = ? WHERE id = ?
                ''', (datetime.now(), existing_user['id']))
                conn.commit()
                conn.close()
                
                return existing_user['id']
            else:
                # 새 사용자 생성
                user_id = self.db_manager.create_user(user_name, user_role)
                logger.info(f"새 사용자 생성: {user_name} ({user_role})")
                return user_id
                
        except Exception as e:
            logger.error(f"사용자 생성 중 오류: {str(e)}")
            raise
    
    def sync_instructor_courses(self, instructor_id: str):
        """교수자 강의 정보 동기화"""
        try:
            if 'courses' not in st.session_state:
                return
            
            session_courses = st.session_state.courses
            
            for course_id, course_data in session_courses.items():
                # 해당 교수자의 강의만 처리
                if course_data.get('instructor') == get_user_name():
                    # 데이터베이스에 강의 존재 여부 확인
                    existing_courses = self.db_manager.get_courses_by_instructor(instructor_id)
                    existing_course_codes = [c['code'] for c in existing_courses]
                    
                    if course_data['code'] not in existing_course_codes:
                        # 새 강의 생성
                        db_course_id = self.db_manager.create_course(
                            name=course_data['name'],
                            code=course_data['code'],
                            instructor_id=instructor_id,
                            semester=course_data['semester'],
                            credit=course_data['credit'],
                            max_students=course_data['max_students'],
                            department=course_data.get('department', ''),
                            description=course_data.get('description', '')
                        )
                        
                        # 세션 강의 ID를 DB 강의 ID로 매핑
                        if 'course_id_mapping' not in st.session_state:
                            st.session_state.course_id_mapping = {}
                        st.session_state.course_id_mapping[course_id] = db_course_id
                        
                        logger.info(f"강의 동기화 완료: {course_data['name']}")
                        
        except Exception as e:
            logger.error(f"교수자 강의 동기화 중 오류: {str(e)}")
    
    def sync_student_enrollments(self, student_id: str):
        """학생 수강신청 정보 동기화"""
        try:
            if 'course_enrollments' not in st.session_state:
                return
            
            session_enrollments = st.session_state.course_enrollments
            
            for course_id, enrollments in session_enrollments.items():
                for enrollment in enrollments:
                    if enrollment['name'] == get_user_name():
                        # 데이터베이스에서 강의 ID 찾기
                        db_course_id = self.get_db_course_id(course_id)
                        
                        if db_course_id:
                            # 수강신청 정보 동기화
                            self.db_manager.enroll_student(student_id, db_course_id)
                            logger.info(f"수강신청 동기화 완료: {course_id}")
                        
        except Exception as e:
            logger.error(f"학생 수강신청 동기화 중 오류: {str(e)}")
    
    def sync_course_materials(self):
        """강의 자료 동기화"""
        try:
            if 'course_materials' not in st.session_state:
                return
            
            session_materials = st.session_state.course_materials
            user_name = get_user_name()
            
            for course_id, materials in session_materials.items():
                db_course_id = self.get_db_course_id(course_id)
                
                if not db_course_id:
                    continue
                
                # 업로더 정보 확인
                uploader = self.db_manager.get_user_by_name_role(user_name, get_user_role())
                if not uploader:
                    continue
                
                # 기존 문서 목록 조회
                existing_docs = self.db_manager.get_course_documents(db_course_id)
                existing_filenames = [doc['filename'] for doc in existing_docs]
                
                for material in materials:
                    if material['name'] not in existing_filenames:
                        # 새 문서 정보 생성
                        doc_id = self.db_manager.create_document(
                            filename=material['name'],
                            original_filename=material['name'],
                            file_path=f"temp/{material['name']}",  # 임시 경로
                            file_type=material.get('type', 'unknown'),
                            file_size=material.get('size', 0),
                            course_id=db_course_id,
                            uploaded_by=uploader['id']
                        )
                        
                        logger.info(f"문서 동기화 완료: {material['name']}")
                        
        except Exception as e:
            logger.error(f"강의 자료 동기화 중 오류: {str(e)}")
    
    def get_db_course_id(self, session_course_id: str) -> Optional[str]:
        """세션 강의 ID를 데이터베이스 강의 ID로 변환"""
        try:
            # 매핑 테이블 확인
            if 'course_id_mapping' in st.session_state:
                if session_course_id in st.session_state.course_id_mapping:
                    return st.session_state.course_id_mapping[session_course_id]
            
            # 세션 강의 정보로 데이터베이스 검색
            if 'courses' in st.session_state:
                session_course = st.session_state.courses.get(session_course_id)
                if session_course:
                    # 강의 코드로 데이터베이스 검색
                    conn = self.db_manager.get_connection()
                    cursor = conn.cursor()
                    cursor.execute('SELECT id FROM courses WHERE code = ?', (session_course['code'],))
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result:
                        db_course_id = result[0]
                        
                        # 매핑 정보 저장
                        if 'course_id_mapping' not in st.session_state:
                            st.session_state.course_id_mapping = {}
                        st.session_state.course_id_mapping[session_course_id] = db_course_id
                        
                        return db_course_id
            
            return None
            
        except Exception as e:
            logger.error(f"강의 ID 변환 중 오류: {str(e)}")
            return None
    
    def migrate_uploaded_files(self, course_id: str, uploaded_files: List) -> List[str]:
        """업로드된 파일을 데이터베이스 시스템으로 이관"""
        try:
            user_name = get_user_name()
            user_role = get_user_role()
            
            if not user_name or not user_role:
                return []
            
            # 사용자 정보 확인
            user = self.db_manager.get_user_by_name_role(user_name, user_role)
            if not user:
                user_id = self.ensure_user_exists(user_name, user_role)
                user = self.db_manager.get_user(user_id)
            
            # 데이터베이스 강의 ID 확인
            db_course_id = self.get_db_course_id(course_id)
            if not db_course_id:
                return []
            
            document_ids = []
            
            for uploaded_file in uploaded_files:
                try:
                    # 파일 저장
                    file_path, metadata = self.document_processor.save_uploaded_file(
                        uploaded_file, db_course_id, user['id']
                    )
                    
                    # 데이터베이스에 문서 정보 저장
                    doc_id = self.db_manager.create_document(
                        filename=metadata['saved_filename'],
                        original_filename=metadata['original_filename'],
                        file_path=file_path,
                        file_type=metadata['file_type'],
                        file_size=metadata['file_size'],
                        course_id=db_course_id,
                        uploaded_by=user['id']
                    )
                    
                    document_ids.append(doc_id)
                    logger.info(f"파일 이관 완료: {uploaded_file.name}")
                    
                except Exception as e:
                    logger.error(f"파일 이관 중 오류: {uploaded_file.name} - {str(e)}")
                    continue
            
            return document_ids
            
        except Exception as e:
            logger.error(f"파일 이관 중 오류: {str(e)}")
            return []
    
    def get_user_courses_for_search(self, user_name: str, user_role: str) -> List[Dict]:
        """사용자의 검색 가능한 강의 목록 반환"""
        try:
            # 데이터베이스 동기화
            user_id = self.ensure_user_exists(user_name, user_role)
            
            if user_role == "instructor":
                courses = self.db_manager.get_courses_by_instructor(user_id)
            elif user_role == "student":
                courses = self.db_manager.get_student_courses(user_id)
            else:
                return []
            
            return courses
            
        except Exception as e:
            logger.error(f"사용자 강의 목록 조회 중 오류: {str(e)}")
            return []
    
    def cleanup_temp_data(self):
        """임시 데이터 정리"""
        try:
            # 세션 매핑 정보 정리
            if 'course_id_mapping' in st.session_state:
                del st.session_state.course_id_mapping
            
            logger.info("임시 데이터 정리 완료")
            
        except Exception as e:
            logger.error(f"임시 데이터 정리 중 오류: {str(e)}")

# 전역 브릿지 인스턴스
@st.cache_resource
def get_system_bridge():
    """시스템 브릿지 인스턴스 반환 (캐시됨)"""
    return SystemBridge() 