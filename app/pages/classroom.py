import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# 현재 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from database.models import DatabaseManager
from utils.session_utils import get_user_role, get_selected_course_id
from pages.chat import show_chat_page
from services.document_service import DocumentService
import pandas as pd
import os

def show_classroom_page():
    """강의실 페이지"""
    
    # 현재 선택된 강의 정보 가져오기
    course_info = st.session_state.get('current_course', {})
    if not course_info:
        st.error("강의 정보를 찾을 수 없습니다. '내 강의' 페이지로 돌아갑니다.")
        if st.button("돌아가기"):
            del st.session_state['current_course']
            st.rerun()
        return
    
    course_data = course_info.get('data', {})
    
    # 페이지 헤더
    st.markdown(f"# 🏛️ {course_data.get('name', '강의실')}")
    st.caption(f"**강의코드:** {course_data.get('code', 'N/A')} | **교수:** {course_data.get('instructor_name', 'N/A')}")
    st.markdown("---")
    
    # 강의실 메뉴 (탭)
    tab_options = ["📢 공지사항", "📚 강의자료", "💬 AI 채팅", "📝 과제", "✅ 출석"]
    tab_icons = ["megaphone", "book", "chat-dots", "file-earmark-text", "check-circle"]
    
    selected_tab = st.tabs(tab_options)
    
    with selected_tab[0]:
        show_announcements()
        
    with selected_tab[1]:
        show_course_materials()
        
    with selected_tab[2]:
        st.session_state.selected_course_id = course_data.get('id')
        show_chat_page()
        
    with selected_tab[3]:
        show_assignments()
        
    with selected_tab[4]:
        show_attendance()
        
    # 강의실 나가기 버튼
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 강의실 나가기", use_container_width=True):
        # 현재 강의 정보 초기화
        st.session_state.current_course = None
        st.session_state.selected_course_id = None
        st.success("강의실에서 나왔습니다.")
        st.rerun()

def show_announcements():
    """공지사항 탭"""
    st.markdown("### 📢 공지사항")
    st.info("공지사항 기능은 개발 중입니다.")

def show_course_materials():
    """강의자료 탭"""
    st.markdown("### 📚 강의자료")

    course_id = get_selected_course_id()
    if not course_id:
        st.warning("강의를 먼저 선택해주세요.")
        return

    doc_service = DocumentService()
    documents = doc_service.get_documents_for_course(course_id)

    if not documents:
        st.info("업로드된 강의자료가 없습니다.")
        return

    # 컬럼 헤더
    col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 1])
    with col1:
        st.markdown("**파일명**")
    with col2:
        st.markdown("**타입**")
    with col3:
        st.markdown("**업로드 날짜**")
    with col4:
        st.markdown("**업로더**")
    with col5:
        st.markdown("**다운로드**")
    
    st.markdown("---")

    # 자료 목록 표시
    for doc in documents:
        col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 1])
        with col1:
            st.markdown(doc['original_filename'])
            if not doc['is_vectorized']:
                st.caption("⏳ AI 학습 데이터 준비 중...")
        with col2:
            st.markdown(doc['file_type'])
        with col3:
            st.markdown(doc['uploaded_at'].split(" ")[0])
        with col4:
            st.markdown(doc['uploader_name'])
        with col5:
            file_path = doc['file_path']
            if os.path.exists(file_path):
                with open(file_path, "rb") as file:
                    st.download_button(
                        label="📥",
                        data=file,
                        file_name=doc['original_filename'],
                        key=f"download_{doc['id']}"
                    )
            else:
                st.error("파일 없음")

def show_assignments():
    """과제 탭"""
    st.markdown("### 📝 과제")
    st.info("과제 제출 및 확인 기능은 개발 중입니다.")

def show_attendance():
    """출석 탭"""
    st.markdown("### ✅ 출석")
    st.info("출석 확인 기능은 개발 중입니다.") 