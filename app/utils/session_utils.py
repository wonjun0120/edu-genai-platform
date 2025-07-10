import streamlit as st

def init_session_state():
    """세션 상태 초기화"""
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    
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

def clear_session():
    """세션 초기화"""
    for key in list(st.session_state.keys()):
        del st.session_state[key] 