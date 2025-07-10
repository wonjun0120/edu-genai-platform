import streamlit as st
from utils.session_utils import get_user_role, get_user_name, clear_session

def show_header():
    """공통 헤더 표시"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_role = get_user_role()
        user_name = get_user_name()
        
        role_text = {
            "student": "학습자",
            "instructor": "교수자", 
            "admin": "관리자"
        }.get(user_role, "사용자")
        
        if user_name:
            st.markdown(f"### 👋 안녕하세요, **{user_name}**님! ({role_text})")
        else:
            st.markdown(f"### 👋 안녕하세요, **{role_text}**님!")
    
    with col2:
        if st.button("🚪 로그아웃", key="logout"):
            clear_session()
            st.rerun()
    
    st.markdown("---") 