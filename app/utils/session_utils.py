import streamlit as st
import uuid
from database.models import DatabaseManager

def init_session_state():
    """세션 상태 초기화"""
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    # 파일 관련 세션 상태
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    
    # 강의 관련 세션 상태
    if 'courses' not in st.session_state:
        st.session_state.courses = {}
    
    if 'course_enrollments' not in st.session_state:
        st.session_state.course_enrollments = {}
    
    if 'course_materials' not in st.session_state:
        st.session_state.course_materials = {}
    
    if 'selected_course_id' not in st.session_state:
        st.session_state.selected_course_id = None
    
    # 채팅 관련 세션 상태
    if 'current_chat_room' not in st.session_state:
        st.session_state.current_chat_room = None
    
    if 'chat_rooms' not in st.session_state:
        st.session_state.chat_rooms = []

def get_user_role():
    """현재 사용자 역할 반환"""
    return st.session_state.get('user_role')

def set_user_role(role):
    """사용자 역할 설정"""
    st.session_state.user_role = role

def get_user_name():
    """현재 사용자 이름 반환"""
    return st.session_state.get('user_name')

def set_user_name(name):
    """사용자 이름 설정"""
    st.session_state.user_name = name

def get_user_id():
    """현재 사용자 ID 반환 (없으면 새로 생성)"""
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        # 사용자 역할과 이름이 있으면 데이터베이스에서 사용자 조회/생성
        if st.session_state.get('user_role') and st.session_state.get('user_name'):
            db_manager = DatabaseManager()
            user = db_manager.get_user_by_name_role(
                st.session_state.user_name, 
                st.session_state.user_role
            )
            
            if user:
                st.session_state.user_id = user['id']
            else:
                # 새 사용자 생성
                st.session_state.user_id = db_manager.create_user(
                    name=st.session_state.user_name,
                    role=st.session_state.user_role
                )
        else:
            # 임시 사용자 ID 생성
            st.session_state.user_id = str(uuid.uuid4())
    
    return st.session_state.user_id

def set_user_id(user_id):
    """사용자 ID 설정"""
    st.session_state.user_id = user_id

def get_selected_course_id():
    """선택된 강의 ID 반환"""
    return st.session_state.get('selected_course_id')

def set_selected_course_id(course_id):
    """선택된 강의 ID 설정"""
    st.session_state.selected_course_id = course_id

def get_current_chat_room():
    """현재 채팅방 ID 반환"""
    return st.session_state.get('current_chat_room')

def set_current_chat_room(room_id):
    """현재 채팅방 ID 설정"""
    st.session_state.current_chat_room = room_id

def get_user_courses():
    """사용자 강의 목록 반환"""
    if not st.session_state.get('user_id'):
        return []
    
    db_manager = DatabaseManager()
    user_role = get_user_role()
    
    if user_role == 'student':
        return db_manager.get_student_courses(st.session_state.user_id)
    elif user_role == 'instructor':
        return db_manager.get_courses_by_instructor(st.session_state.user_id)
    else:
        return []

def clear_session():
    """세션 초기화"""
    for key in list(st.session_state.keys()):
        del st.session_state[key] 