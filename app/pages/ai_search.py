import streamlit as st
import asyncio
import time
from typing import Dict, List
import sys
from pathlib import Path

# 현재 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from database.models import DatabaseManager
from vector.faiss_manager import FAISSVectorManager
from processing.document_processor import DocumentProcessor
from ai.search_engine import AISearchEngine
from utils.session_utils import get_user_name, get_user_role

# 전역 변수로 AI 검색 엔진 초기화
@st.cache_resource
def get_ai_search_engine():
    """AI 검색 엔진 인스턴스 반환 (캐시됨)"""
    return AISearchEngine()

def show_ai_search_page():
    """AI 검색 페이지 메인"""
    st.markdown("### 🔍 AI 검색")
    
    user_role = get_user_role()
    user_name = get_user_name()
    
    if not user_name:
        st.error("사용자 정보를 찾을 수 없습니다.")
        return
    
    # AI 검색 엔진 초기화
    search_engine = get_ai_search_engine()
    
    # 사용자별 강의 목록 조회
    if user_role == "instructor":
        courses = get_instructor_courses(user_name)
    elif user_role == "student":
        courses = get_student_courses(user_name)
    else:
        st.error("지원되지 않는 사용자 역할입니다.")
        return
    
    if not courses:
        st.info("검색할 수 있는 강의가 없습니다.")
        return
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["🔍 검색", "📊 통계", "🔧 관리"])
    
    with tab1:
        show_search_tab(search_engine, courses, user_name)
    
    with tab2:
        show_statistics_tab(search_engine, courses)
    
    with tab3:
        if user_role == "instructor":
            show_management_tab(search_engine, courses)
        else:
            st.info("관리 기능은 교수자만 사용할 수 있습니다.")

def show_search_tab(search_engine: AISearchEngine, courses: List[Dict], user_name: str):
    """검색 탭"""
    st.markdown("#### 강의 자료 검색")
    
    # 강의 선택
    course_options = {f"{course['name']} ({course['code']})": course['id'] for course in courses}
    selected_course_name = st.selectbox("강의 선택", list(course_options.keys()))
    
    if not selected_course_name:
        return
    
    selected_course_id = course_options[selected_course_name]
    
    # 검색 설정
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("검색어를 입력하세요", placeholder="예: 인공지능, 머신러닝, 딥러닝")
    
    with col2:
        search_type = st.selectbox("검색 방식", ["vector", "keyword", "hybrid"], 
                                 format_func=lambda x: {"vector": "🧠 벡터 검색", 
                                                       "keyword": "🔤 키워드 검색", 
                                                       "hybrid": "🔄 하이브리드"}[x])
    
    # 고급 설정
    with st.expander("🔧 고급 검색 설정"):
        col1, col2 = st.columns(2)
        
        with col1:
            top_k = st.slider("결과 개수", min_value=1, max_value=20, value=5)
        
        with col2:
            min_similarity = st.slider("최소 유사도", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
    
    # 검색 실행
    if st.button("🔍 검색", type="primary", use_container_width=True):
        if search_query.strip():
            with st.spinner("검색 중..."):
                results = search_engine.search_documents(
                    course_id=selected_course_id,
                    query=search_query.strip(),
                    user_id=user_name,
                    search_type=search_type,
                    top_k=top_k,
                    min_similarity=min_similarity
                )
                
                display_search_results(results, search_type)
        else:
            st.warning("검색어를 입력해주세요.")
    
    # 검색 제안어
    if search_query and len(search_query) > 1:
        suggestions = search_engine.get_search_suggestions(selected_course_id, search_query)
        if suggestions:
            st.markdown("**💡 검색 제안어:**")
            suggestion_cols = st.columns(min(len(suggestions), 5))
            for i, suggestion in enumerate(suggestions[:5]):
                with suggestion_cols[i]:
                    if st.button(f"📝 {suggestion}", key=f"suggest_{i}"):
                        st.session_state.search_query = suggestion
                        st.rerun()
    
    # 최근 검색 기록
    show_recent_searches(search_engine, user_name)

def display_search_results(results: Dict, search_type: str):
    """검색 결과 표시"""
    if not results['success']:
        st.error(f"검색 중 오류가 발생했습니다: {results.get('error', '알 수 없는 오류')}")
        return
    
    if results['result_count'] == 0:
        st.info("검색 결과가 없습니다. 다른 검색어를 시도해보세요.")
        return
    
    # 검색 결과 헤더
    st.markdown(f"### 📋 검색 결과 ({results['result_count']}개)")
    st.caption(f"검색 시간: {results.get('search_time', 0):.2f}초 | 검색 방식: {search_type}")
    
    # 검색 결과 표시
    for i, result in enumerate(results['results']):
        with st.expander(f"📄 {result['filename']} ({result['file_type']})", expanded=i < 3):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**📝 내용 미리보기:**")
                st.markdown(f"```\n{result['text_preview']}\n```")
                
                if 'similarity' in result:
                    st.progress(result['similarity'], text=f"유사도: {result['similarity']:.2f}")
                
                if 'keyword_count' in result:
                    st.info(f"키워드 출현 횟수: {result['keyword_count']}회")
                
                if 'hybrid_score' in result:
                    st.progress(result['hybrid_score'], text=f"하이브리드 점수: {result['hybrid_score']:.2f}")
            
            with col2:
                st.markdown(f"**📁 파일 정보:**")
                st.write(f"• 업로더: {result['uploader']}")
                st.write(f"• 업로드: {result['uploaded_at']}")
                st.write(f"• 타입: {result['file_type']}")
                
                if st.button("📎 파일 열기", key=f"open_{result['document_id']}"):
                    st.info("파일 다운로드 기능은 추후 구현 예정입니다.")

def show_statistics_tab(search_engine: AISearchEngine, courses: List[Dict]):
    """통계 탭"""
    st.markdown("#### 📊 검색 통계")
    
    # 강의별 통계
    for course in courses:
        with st.expander(f"📚 {course['name']} ({course['code']})"):
            stats = search_engine.get_course_search_stats(course['id'])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("전체 문서", stats['total_documents'])
                st.metric("처리된 문서", stats['processed_documents'])
            
            with col2:
                st.metric("벡터화된 문서", stats['vectorized_documents'])
                st.metric("처리율", f"{stats['processing_rate']:.1f}%")
            
            with col3:
                st.metric("벡터화율", f"{stats['vectorization_rate']:.1f}%")
                if stats['vector_stats'].get('chunk_count', 0) > 0:
                    st.metric("검색 청크 수", stats['vector_stats']['chunk_count'])
            
            # 인덱스 정보
            if stats['vector_stats']:
                st.markdown("**🧠 벡터 인덱스 정보:**")
                vector_stats = stats['vector_stats']
                st.write(f"• 임베딩 모델: {vector_stats.get('embedding_model', 'N/A')}")
                st.write(f"• 벡터 차원: {vector_stats.get('dimension', 'N/A')}")
                st.write(f"• 인덱스 크기: {vector_stats.get('index_size_mb', 0):.2f} MB")

def show_management_tab(search_engine: AISearchEngine, courses: List[Dict]):
    """관리 탭 (교수자 전용)"""
    st.markdown("#### 🔧 인덱스 관리")
    
    # 강의 선택
    course_options = {f"{course['name']} ({course['code']})": course['id'] for course in courses}
    selected_course_name = st.selectbox("관리할 강의 선택", list(course_options.keys()), key="manage_course")
    
    if not selected_course_name:
        return
    
    selected_course_id = course_options[selected_course_name]
    
    # 인덱싱 관리
    st.markdown("##### 📚 문서 인덱싱")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 인덱스 업데이트", type="primary"):
            with st.spinner("인덱싱 중..."):
                result = asyncio.run(search_engine.index_course_documents(selected_course_id))
                
                if result['success']:
                    st.success(result['message'])
                    st.info(f"처리 시간: {result.get('processing_time', 0):.2f}초")
                else:
                    st.error(result['message'])
    
    with col2:
        if st.button("🔄 강제 재인덱싱", type="secondary"):
            with st.spinner("재인덱싱 중..."):
                result = asyncio.run(search_engine.index_course_documents(selected_course_id, force_reindex=True))
                
                if result['success']:
                    st.success(result['message'])
                    st.info(f"처리 시간: {result.get('processing_time', 0):.2f}초")
                else:
                    st.error(result['message'])
    
    # 인덱스 상태 표시
    st.markdown("##### 📊 현재 인덱스 상태")
    stats = search_engine.get_course_search_stats(selected_course_id)
    
    if stats['total_documents'] > 0:
        progress_val = stats['vectorization_rate'] / 100
        st.progress(progress_val, text=f"벡터화 진행률: {stats['vectorization_rate']:.1f}%")
        
        st.markdown("**📋 상세 정보:**")
        st.write(f"• 전체 문서: {stats['total_documents']}개")
        st.write(f"• 처리된 문서: {stats['processed_documents']}개")
        st.write(f"• 벡터화된 문서: {stats['vectorized_documents']}개")
        
        if stats['vector_stats']:
            st.write(f"• 검색 청크: {stats['vector_stats'].get('chunk_count', 0)}개")
            st.write(f"• 인덱스 크기: {stats['vector_stats'].get('index_size_mb', 0):.2f} MB")
    else:
        st.info("아직 업로드된 문서가 없습니다.")

def show_recent_searches(search_engine: AISearchEngine, user_name: str):
    """최근 검색 기록 표시"""
    with st.expander("🕐 최근 검색 기록"):
        history = search_engine.get_user_search_history(user_name, limit=5)
        
        if history:
            for search in history:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"🔍 {search['query']}")
                
                with col2:
                    search_type_icon = {"vector": "🧠", "keyword": "🔤", "hybrid": "🔄"}
                    st.write(f"{search_type_icon.get(search['search_type'], '❓')} {search['search_type']}")
                
                with col3:
                    st.write(f"📄 {search['results_count']}개")
        else:
            st.info("검색 기록이 없습니다.")

def get_instructor_courses(instructor_name: str) -> List[Dict]:
    """교수자의 강의 목록 조회"""
    try:
        db_manager = DatabaseManager()
        
        # 교수자 정보 조회
        user = db_manager.get_user_by_name_role(instructor_name, "instructor")
        if not user:
            return []
        
        # 강의 목록 조회
        courses = db_manager.get_courses_by_instructor(user['id'])
        return courses
        
    except Exception as e:
        st.error(f"강의 목록 조회 중 오류: {str(e)}")
        return []

def get_student_courses(student_name: str) -> List[Dict]:
    """학생의 수강 강의 목록 조회"""
    try:
        db_manager = DatabaseManager()
        
        # 학생 정보 조회
        user = db_manager.get_user_by_name_role(student_name, "student")
        if not user:
            return []
        
        # 수강 강의 목록 조회
        courses = db_manager.get_student_courses(user['id'])
        return courses
        
    except Exception as e:
        st.error(f"수강 강의 목록 조회 중 오류: {str(e)}")
        return [] 