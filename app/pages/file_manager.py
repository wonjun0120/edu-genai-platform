import streamlit as st
import pandas as pd
from utils.file_utils import handle_file_upload, get_uploaded_files

def show_file_manager():
    """파일 관리 페이지"""
    st.markdown("### 📁 파일 관리")
    
    # 파일 업로드 섹션
    st.markdown("#### 📤 파일 업로드")
    
    # 업로드 설정
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "파일을 선택하세요 (여러 파일 동시 업로드 가능):",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'docx', 'pptx', 'xlsx', 'csv', 'md', 'py', 'js', 'html', 'css']
        )
    
    with col2:
        st.markdown("**지원 파일 형식:**")
        st.markdown("""
        - 📄 문서: PDF, DOCX, TXT, MD
        - 📊 스프레드시트: XLSX, CSV
        - 🎨 프레젠테이션: PPTX
        - 💻 코드: PY, JS, HTML, CSS
        """)
    
    # 파일 업로드 처리
    if uploaded_files:
        with st.spinner("파일 업로드 중..."):
            saved_files = handle_file_upload(uploaded_files)
            if saved_files:
                st.success(f"✅ {len(saved_files)}개 파일이 성공적으로 업로드되었습니다!")
                
                # 업로드된 파일 정보 표시
                for file_info in saved_files:
                    with st.expander(f"📄 {file_info['name']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**크기:** {file_info['size']} bytes")
                            st.write(f"**유형:** {file_info['type']}")
                        with col2:
                            st.write(f"**업로드 시간:** {file_info['uploaded_at']}")
                            st.write(f"**저장 경로:** {file_info['path']}")
    
    st.markdown("---")
    
    # 업로드된 파일 목록
    uploaded_files_list = get_uploaded_files()
    
    if uploaded_files_list:
        st.markdown("#### 📋 업로드된 파일 목록")
        
        # 파일 목록을 DataFrame으로 변환
        df_files = pd.DataFrame(uploaded_files_list)
        
        # 파일 크기 포맷팅
        df_files['size_formatted'] = df_files['size'].apply(lambda x: f"{x:,} bytes")
        
        # 컬럼 순서 정리
        display_df = df_files[['name', 'type', 'size_formatted', 'uploaded_at']].copy()
        display_df.columns = ['파일명', '파일 유형', '크기', '업로드 시간']
        
        # 파일 목록 표시
        st.dataframe(display_df, use_container_width=True)
        
        # 파일 관리 옵션
        st.markdown("#### 🛠️ 파일 관리 옵션")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 통계 보기", use_container_width=True):
                show_file_statistics(uploaded_files_list)
        
        with col2:
            if st.button("🔍 파일 검색", use_container_width=True):
                show_file_search(uploaded_files_list)
        
        with col3:
            if st.button("🗑️ 전체 삭제", use_container_width=True):
                if st.session_state.get('confirm_delete', False):
                    st.session_state.uploaded_files = []
                    st.session_state.confirm_delete = False
                    st.success("모든 파일이 삭제되었습니다.")
                    st.rerun()
                else:
                    st.session_state.confirm_delete = True
                    st.warning("한 번 더 클릭하시면 모든 파일이 삭제됩니다.")
    else:
        st.info("📝 업로드된 파일이 없습니다. 위의 파일 업로드 섹션을 이용해 파일을 추가해보세요.")

def show_file_statistics(files):
    """파일 통계 표시"""
    st.markdown("##### 📊 파일 통계")
    
    # 기본 통계
    total_files = len(files)
    total_size = sum(f['size'] for f in files)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("총 파일 수", f"{total_files}개")
        st.metric("총 용량", f"{total_size:,} bytes")
    
    with col2:
        # 파일 타입별 통계
        file_types = {}
        for file in files:
            file_type = file['type']
            if file_type in file_types:
                file_types[file_type] += 1
            else:
                file_types[file_type] = 1
        
        st.markdown("**파일 타입별 개수:**")
        for file_type, count in file_types.items():
            st.write(f"- {file_type}: {count}개")

def show_file_search(files):
    """파일 검색 기능"""
    st.markdown("##### 🔍 파일 검색")
    
    search_term = st.text_input("검색어를 입력하세요:")
    
    if search_term:
        # 파일명으로 검색
        filtered_files = [f for f in files if search_term.lower() in f['name'].lower()]
        
        if filtered_files:
            st.markdown(f"**검색 결과: {len(filtered_files)}개**")
            df_filtered = pd.DataFrame(filtered_files)
            display_df = df_filtered[['name', 'type', 'uploaded_at']].copy()
            display_df.columns = ['파일명', '파일 유형', '업로드 시간']
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("검색 결과가 없습니다.") 