import streamlit as st
import sys
from pathlib import Path
import asyncio
import time

# 현재 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from services.document_service import DocumentService
from utils.session_utils import get_user_name, get_user_role

def show_document_upload():
    """문서 업로드 페이지"""
    st.title("📚 문서 업로드 및 벡터화")
    
    # 사용자 인증 확인
    user_name = get_user_name()
    user_role = get_user_role()
    
    if not user_name or not user_role:
        st.error("로그인이 필요합니다.")
        return
    
    # 문서 서비스 초기화
    if 'document_service' not in st.session_state:
        with st.spinner("문서 서비스 초기화 중..."):
            st.session_state.document_service = DocumentService()
    
    service = st.session_state.document_service
    
    # 강의 선택
    st.subheader("1️⃣ 강의 선택")
    
    # 세션에서 강의 목록 가져오기
    available_courses = []
    if 'courses' in st.session_state:
        if user_role == "instructor":
            # 교수자는 자신의 강의만
            available_courses = [
                (course_id, course_data['name']) 
                for course_id, course_data in st.session_state.courses.items()
                if course_data.get('instructor') == user_name
            ]
        elif user_role == "student":
            # 학생은 수강 중인 강의만
            if 'course_enrollments' in st.session_state:
                enrolled_courses = []
                for course_id, enrollments in st.session_state.course_enrollments.items():
                    for enrollment in enrollments:
                        if enrollment['name'] == user_name:
                            course_name = st.session_state.courses[course_id]['name']
                            enrolled_courses.append((course_id, course_name))
                available_courses = enrolled_courses
    
    if not available_courses:
        st.warning("업로드 가능한 강의가 없습니다.")
        return
    
    # 강의 선택 UI
    course_options = {name: course_id for course_id, name in available_courses}
    selected_course_name = st.selectbox(
        "강의를 선택하세요:",
        options=list(course_options.keys())
    )
    selected_course_id = course_options[selected_course_name]
    
    # 현재 강의 문서 통계 표시
    with st.expander(f"📊 '{selected_course_name}' 강의 문서 현황"):
        stats = service.get_course_document_stats(selected_course_id)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 문서 수", stats['total_documents'])
        with col2:
            st.metric("벡터화 완료", stats['vectorized_documents'])
        with col3:
            st.metric("총 청크 수", stats['total_chunks'])
        with col4:
            st.metric("인덱스 크기(MB)", f"{stats['vector_index_size_mb']:.2f}")
        
        if stats['embedding_model']:
            st.info(f"🤖 임베딩 모델: {stats['embedding_model']} ({stats['vector_dimension']}차원)")
    
    st.subheader("2️⃣ 파일 업로드")
    
    # 지원 파일 형식 안내
    with st.expander("📋 지원되는 파일 형식"):
        supported_formats = service.doc_processor.get_supported_formats()
        st.write("지원 형식:", ", ".join(supported_formats))
        
        format_info = {
            'pdf': '🔴 PDF 문서',
            'docx': '📘 Word 문서 (.docx)',
            'pptx': '📊 PowerPoint 프레젠테이션 (.pptx)', 
            'xlsx': '📗 Excel 스프레드시트 (.xlsx)',
            'txt': '📄 텍스트 파일',
            'csv': '📈 CSV 데이터',
            'md': '📝 마크다운',
            'html': '🌐 HTML 문서'
        }
        
        for fmt, desc in format_info.items():
            if fmt in supported_formats:
                st.write(f"- {desc}")
    
    # 파일 업로드 UI
    uploaded_files = st.file_uploader(
        "업로드할 파일을 선택하세요:",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'pptx', 'xlsx', 'txt', 'csv', 'md', 'html']
    )
    
    if uploaded_files:
        st.subheader("3️⃣ 업로드된 파일 목록")
        
        # 파일 목록 표시
        for i, file in enumerate(uploaded_files):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"📁 {file.name}")
                with col2:
                    st.write(f"{file.size / 1024:.1f} KB")
                with col3:
                    file_type = service.doc_processor.detect_file_type(file.name)
                    st.write(f"📋 {file_type.upper()}")
        
        st.subheader("4️⃣ 처리 옵션")
        
        col1, col2 = st.columns(2)
        with col1:
            process_individually = st.checkbox("개별 처리 (각 파일별 진행상황 표시)", value=True)
        with col2:
            auto_vectorize = st.checkbox("자동 벡터화", value=True)
        
        # 처리 시작 버튼
        if st.button("🚀 파일 처리 시작", type="primary"):
            # 사용자 ID 확인
            user_id = f"{user_name}_{user_role}"
            
            if process_individually:
                # 개별 처리
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, file in enumerate(uploaded_files):
                    status_text.text(f"처리 중: {file.name}")
                    
                    with st.spinner(f"'{file.name}' 처리 중..."):
                        result = service.process_uploaded_file(
                            file, selected_course_id, user_id
                        )
                        results.append(result)
                    
                    # 진행률 업데이트
                    progress = (i + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    
                    # 개별 결과 표시
                    if result['success']:
                        st.success(f"✅ {file.name}: {result['message']}")
                        
                        # 상세 정보 표시
                        with st.expander(f"📊 '{file.name}' 처리 결과"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("텍스트 길이", result['text_length'])
                            with col2:
                                st.metric("단어 수", result['word_count'])
                            with col3:
                                st.metric("청크 수", result['chunk_count'])
                    else:
                        st.error(f"❌ {file.name}: {result['error']}")
                
                status_text.text("✅ 모든 파일 처리 완료!")
                
            else:
                # 일괄 처리 (비동기)
                with st.spinner("모든 파일 일괄 처리 중..."):
                    # 동기적으로 처리 (Streamlit 제한)
                    results = []
                    for file in uploaded_files:
                        result = service.process_uploaded_file(
                            file, selected_course_id, user_id
                        )
                        results.append(result)
                        time.sleep(0.1)  # 시스템 부하 방지
            
            # 최종 결과 요약
            st.subheader("📋 처리 결과 요약")
            
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 파일 수", len(uploaded_files))
            with col2:
                st.metric("성공", len(successful), delta=len(successful))
            with col3:
                st.metric("실패", len(failed), delta=-len(failed) if failed else 0)
            
            if successful:
                total_chunks = sum(r.get('chunk_count', 0) for r in successful)
                total_words = sum(r.get('word_count', 0) for r in successful)
                
                st.success(f"🎉 {len(successful)}개 파일이 성공적으로 처리되었습니다!")
                st.info(f"📊 총 {total_chunks}개 청크, {total_words}개 단어가 벡터화되었습니다.")
            
            if failed:
                st.error(f"❌ {len(failed)}개 파일 처리에 실패했습니다.")
                with st.expander("실패한 파일 목록"):
                    for result in failed:
                        st.write(f"- {result.get('filename', '알 수 없음')}: {result['error']}")
    
    # 검색 테스트 섹션
    st.subheader("🔍 업로드된 문서 검색 테스트")
    
    search_query = st.text_input("검색어를 입력하세요:", placeholder="예: 머신러닝이란 무엇인가요?")
    
    if search_query and st.button("검색"):
        user_id = f"{user_name}_{user_role}"
        
        with st.spinner("검색 중..."):
            search_result = service.search_course_documents(
                course_id=selected_course_id,
                query=search_query,
                user_id=user_id,
                top_k=5
            )
        
        if search_result['success'] and search_result['results']:
            st.success(f"🔍 검색 완료: {search_result['total_count']}개 결과")
            
            for i, result in enumerate(search_result['results']):
                with st.container():
                    st.markdown(f"""
                    **{i+1}. 유사도: {result['similarity']:.3f}**
                    
                    📄 문서 ID: `{result['document_id']}`  
                    📝 내용: {result['text'][:200]}...
                    """)
                    st.divider()
        else:
            st.warning("검색 결과가 없습니다.")

if __name__ == "__main__":
    show_document_upload() 