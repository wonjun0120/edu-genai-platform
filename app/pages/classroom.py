import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# 현재 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from utils.session_utils import get_user_name, get_user_role
from services.document_service import DocumentService
from database.models import DatabaseManager

def show_classroom():
    """강의실 메인 페이지"""
    user_name = get_user_name()
    user_role = get_user_role()
    
    if not user_name or not user_role:
        st.error("로그인이 필요합니다.")
        return
    
    # 강의실 입장 여부 확인
    if 'current_course' not in st.session_state:
        show_course_selection()
    else:
        show_classroom_dashboard()

def show_course_selection():
    """강의 선택 페이지"""
    st.title("🏛️ 강의실 입장")
    st.markdown("---")
    
    user_name = get_user_name()
    user_role = get_user_role()
    
    # 사용자별 강의 목록 가져오기
    available_courses = get_user_courses(user_name, user_role)
    
    if not available_courses:
        st.warning("입장 가능한 강의가 없습니다.")
        
        if user_role == "instructor":
            st.info("💡 먼저 '📚 강의 관리'에서 강의를 개설해주세요.")
        else:
            st.info("💡 먼저 '📚 내 강의'에서 강의를 신청해주세요.")
        return
    
    st.subheader("📚 입장 가능한 강의 목록")
    
    # 강의 카드 형태로 표시
    for course_id, course in available_courses.items():
        with st.container():
            col1, col2, col3 = st.columns([4, 2, 2])
            
            with col1:
                st.markdown(f"### 📖 {course['name']}")
                st.write(f"**강의코드:** {course['code']}")
                st.write(f"**학기:** {course['semester']}")
                instructor_name = course.get('instructor_name', course.get('instructor', 'N/A'))
                st.write(f"**담당교수:** {instructor_name}")
                
                if course.get('description'):
                    with st.expander("강의 설명"):
                        st.write(course['description'])
            
            with col2:
                # 데이터베이스에서 강의 통계 조회
                if 'db_manager' not in st.session_state:
                    st.session_state.db_manager = DatabaseManager()
                
                db_manager = st.session_state.db_manager
                enrolled_count = len(db_manager.get_course_enrollments(course_id))
                materials_count = len(db_manager.get_course_documents(course_id))
                
                st.metric("수강인원", f"{enrolled_count}명")
                st.metric("강의자료", f"{materials_count}개")
            
            with col3:
                st.write("")  # 여백
                if st.button(f"🚪 입장", key=f"enter_{course_id}", type="primary"):
                    enter_classroom(course_id, course)
                
                if user_role == "instructor" and instructor_name == user_name:
                    st.caption("👨‍🏫 내 강의")
                elif user_role == "student":
                    st.caption("👨‍🎓 수강 중")
            
            st.markdown("---")

def get_user_courses(user_name: str, user_role: str) -> dict:
    """사용자별 강의 목록 조회"""
    # 데이터베이스 매니저 초기화
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    available_courses = {}
    
    if user_role == "instructor":
        # 교수자는 자신이 개설한 강의
        instructor = db_manager.get_user_by_name_role(user_name, "instructor")
        if instructor:
            courses_list = db_manager.get_courses_by_instructor(instructor['id'])
            for course in courses_list:
                available_courses[course['id']] = course
    
    elif user_role == "student":
        # 학생은 수강 중인 강의
        student = db_manager.get_user_by_name_role(user_name, "student")
        if student:
            courses_list = db_manager.get_student_courses(student['id'])
            for course in courses_list:
                available_courses[course['id']] = course
    
    return available_courses

def enter_classroom(course_id: str, course: dict):
    """강의실 입장"""
    st.session_state.current_course = {
        'id': course_id,
        'data': course,
        'entered_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    st.success(f"🎉 '{course['name']}' 강의실에 입장했습니다!")
    st.rerun()

def show_classroom_dashboard():
    """강의실 대시보드"""
    current_course = st.session_state.current_course
    course = current_course['data']
    course_id = current_course['id']
    
    # 헤더
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"🏛️ {course['name']} 강의실")
        instructor_name = course.get('instructor_name', course.get('instructor', 'N/A'))
        st.caption(f"강의코드: {course['code']} | 담당교수: {instructor_name}")
    
    with col2:
        if st.button("🚪 강의실 나가기", type="secondary"):
            del st.session_state.current_course
            st.success("🎉 강의실에서 나왔습니다! 강의 관리 페이지로 이동합니다.")
            st.rerun()
    
    st.markdown("---")
    
    # 강의실 메뉴
    user_role = get_user_role()
    
    if user_role == "instructor":
        show_instructor_classroom_menu(course_id, course)
    else:
        show_student_classroom_menu(course_id, course)

def show_instructor_classroom_menu(course_id: str, course: dict):
    """교수자 강의실 메뉴"""
    st.subheader("👨‍🏫 교수자 메뉴")
    
    # 메뉴 탭
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 강의 현황", 
        "📚 강의자료 관리", 
        "🔍 AI 검색", 
        "💬 강의실 채팅", 
        "📈 수업 분석",
        "⚙️ 강의 설정"
    ])
    
    with tab1:
        show_course_overview(course_id, course)
    
    with tab2:
        show_course_materials_manager(course_id, course)
    
    with tab3:
        show_classroom_ai_search(course_id, course)
    
    with tab4:
        show_classroom_chat(course_id, course)
    
    with tab5:
        show_course_analytics(course_id, course)
    
    with tab6:
        show_course_settings(course_id, course)

def show_student_classroom_menu(course_id: str, course: dict):
    """학생 강의실 메뉴"""
    st.subheader("👨‍🎓 학습자 메뉴")
    
    # 메뉴 탭
    tab1, tab2, tab3, tab4 = st.tabs([
        "📚 강의자료", 
        "🔍 AI 검색", 
        "💬 질문/토론", 
        "📝 학습노트"
    ])
    
    with tab1:
        show_course_materials_view(course_id, course)
    
    with tab2:
        show_classroom_ai_search(course_id, course)
    
    with tab3:
        show_classroom_chat(course_id, course)
    
    with tab4:
        show_student_notes(course_id, course)

def show_course_overview(course_id: str, course: dict):
    """강의 현황 (교수자용)"""
    st.markdown("### 📊 강의 현황")
    
    # 기본 정보
    col1, col2, col3, col4 = st.columns(4)
    
    # 데이터베이스에서 강의 정보 조회
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    enrolled_students = db_manager.get_course_enrollments(course_id)
    materials_count = len(db_manager.get_course_documents(course_id))
    
    with col1:
        st.metric("수강인원", f"{len(enrolled_students)}명", f"/{course['max_students']}")
    
    with col2:
        st.metric("강의자료", f"{materials_count}개")
    
    with col3:
        st.metric("학점", f"{course['credit']}학점")
    
    with col4:
        st.metric("개설학과", course.get('department', 'N/A'))
    
    # 수강생 목록
    if enrolled_students:
        st.markdown("#### 👥 수강생 목록")
        
        students_df = []
        for student in enrolled_students:
            students_df.append({
                '이름': student['name'],
                '수강신청일': student['enrolled_at'],
                '상태': student.get('status', '수강중')
            })
        
        if students_df:
            import pandas as pd
            df = pd.DataFrame(students_df)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("아직 수강신청한 학생이 없습니다.")

def show_course_materials_manager(course_id: str, course: dict):
    """강의자료 관리 (교수자용)"""
    st.markdown("### 📚 강의자료 관리")
    
    # 문서 서비스 초기화
    if 'document_service' not in st.session_state:
        with st.spinner("문서 서비스 초기화 중..."):
            st.session_state.document_service = DocumentService()
    
    service = st.session_state.document_service
    
    # 현재 강의 자료 통계
    with st.expander("📊 강의자료 현황"):
        stats = service.get_course_document_stats(course_id)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 문서 수", stats['total_documents'])
        with col2:
            st.metric("벡터화 완료", stats['vectorized_documents'])
        with col3:
            st.metric("총 청크 수", stats['total_chunks'])
        with col4:
            st.metric("인덱스 크기(MB)", f"{stats['vector_index_size_mb']:.2f}")
    
    # 파일 업로드 섹션
    st.markdown("#### 📤 새 강의자료 업로드")
    
    uploaded_files = st.file_uploader(
        "강의자료를 선택하세요:",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'pptx', 'xlsx', 'txt', 'csv', 'md', 'html'],
        help="PDF, Word, PowerPoint, Excel, 텍스트 파일을 업로드할 수 있습니다."
    )
    
    if uploaded_files:
        col1, col2 = st.columns(2)
        with col1:
            auto_vectorize = st.checkbox("자동 벡터화 (AI 검색 활성화)", value=True)
        with col2:
            st.write("")  # 여백
        
        if st.button("📤 업로드 및 처리", type="primary"):
            # 실제 사용자 ID 얻기
            from database.models import DatabaseManager
            db = DatabaseManager()
            user_data = db.get_user_by_name_role(get_user_name(), get_user_role())
            
            if user_data:
                user_id = user_data['id']
            else:
                # 사용자가 없으면 생성
                user_id = db.create_user(get_user_name(), get_user_role())
                st.info(f"새 사용자 계정이 생성되었습니다: {get_user_name()}")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 결과 메시지를 저장할 컨테이너
            success_container = st.empty()
            error_container = st.empty()
            
            results = []
            for i, file in enumerate(uploaded_files):
                status_text.text(f"처리 중: {file.name}")
                
                result = service.process_uploaded_file(file, course_id, user_id)
                results.append(result)
                
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
            
            status_text.text("✅ 모든 파일 처리 완료!")
            
            # 결과 요약
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            if successful:
                success_container.success(f"🎉 {len(successful)}개 파일이 성공적으로 업로드되었습니다!")
                
                # 업로드 성공 메시지 표시 시간 기록
                import time
                st.session_state.upload_success_time = time.time()
                
                # 성공적으로 업로드된 파일들의 정보 저장
                st.session_state.recent_uploads = [
                    {
                        'name': r.get('file_name', ''),
                        'status': '성공',
                        'time': time.time()
                    } for r in successful
                ]
            
            if failed:
                error_messages = []
                for r in failed:
                    error_messages.append(f"❌ {r.get('file_name', 'Unknown')}: {r['error']}")
                error_container.error("\n".join(error_messages))
    
    # 최근 업로드 성공 메시지 표시 (일정 시간 후 자동으로 숨김)
    import time
    if 'upload_success_time' in st.session_state:
        elapsed_time = time.time() - st.session_state.upload_success_time
        if elapsed_time < 5:  # 5초 동안만 표시
            st.success("✅ 파일 업로드가 완료되었습니다!")
        else:
            # 5초 후 메시지 제거
            del st.session_state.upload_success_time
    
    # 기존 자료 목록
    st.markdown("#### 📋 업로드된 강의자료")
    
    # 데이터베이스에서 강의자료 목록 가져오기
    try:
        from database.models import DatabaseManager
        import pandas as pd
        import os
        
        db = DatabaseManager()
        documents = db.get_course_documents(course_id)
        
        if documents:
            st.markdown(f"##### 총 {len(documents)}개의 강의자료")
                       
            # 문서 데이터 처리
            table_data = []
            for doc in documents:
                # 파일 타입에 따른 아이콘 설정
                file_type = doc.get('file_type', '').lower()
                if 'pdf' in file_type:
                    icon = "📄"
                elif 'word' in file_type or 'docx' in file_type:
                    icon = "📝"
                elif 'excel' in file_type or 'xlsx' in file_type:
                    icon = "📊"
                elif 'powerpoint' in file_type or 'pptx' in file_type:
                    icon = "📊"
                elif 'image' in file_type:
                    icon = "🖼️"
                else:
                    icon = "📄"
                
                # 파일 크기 계산
                file_size_kb = doc['file_size'] / 1024
                if file_size_kb < 1024:
                    size_str = f"{file_size_kb:.1f} KB"
                else:
                    size_str = f"{file_size_kb/1024:.1f} MB"
                
                # 벡터화 상태
                ai_status = "🔍 가능" if doc.get('is_vectorized', False) else "⏳ 처리중"
                
                table_data.append({
                    'ID': doc['id'],
                    '타입': icon,
                    '파일명': doc['original_filename'],
                    '크기': size_str,
                    '업로드일': doc['uploaded_at'][:16],  # 날짜만 표시
                    '업로드자': doc['uploader_name'],
                    'AI검색': ai_status,
                    '파일경로': doc['file_path'],
                    '파일크기원본': doc['file_size']
                })
                    
            # 정렬 상태 초기화
            if 'sort_column' not in st.session_state:
                st.session_state.sort_column = '업로드일'
            if 'sort_ascending' not in st.session_state:
                st.session_state.sort_ascending = False
            
            # 파일 헤더 (정렬 버튼 포함)
            st.markdown("---")
            
            col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 3, 1, 1.5, 1, 1, 1.5])
            with col1:
                st.markdown("**타입**")
            with col2:
                if st.button("**파일명** ↕️", key="sort_filename", help="파일명으로 정렬"):
                    if st.session_state.sort_column == '파일명':
                        st.session_state.sort_ascending = not st.session_state.sort_ascending
                    else:
                        st.session_state.sort_column = '파일명'
                        st.session_state.sort_ascending = True
                    st.rerun()
            with col3:
                if st.button("**크기** ↕️", key="sort_size", help="크기로 정렬"):
                    if st.session_state.sort_column == '크기':
                        st.session_state.sort_ascending = not st.session_state.sort_ascending
                    else:
                        st.session_state.sort_column = '크기'
                        st.session_state.sort_ascending = True
                    st.rerun()
            with col4:
                if st.button("**업로드일** ↕️", key="sort_date", help="업로드일로 정렬"):
                    if st.session_state.sort_column == '업로드일':
                        st.session_state.sort_ascending = not st.session_state.sort_ascending
                    else:
                        st.session_state.sort_column = '업로드일'
                        st.session_state.sort_ascending = True
                    st.rerun()
            with col5:
                if st.button("**업로드자** ↕️", key="sort_uploader", help="업로드자로 정렬"):
                    if st.session_state.sort_column == '업로드자':
                        st.session_state.sort_ascending = not st.session_state.sort_ascending
                    else:
                        st.session_state.sort_column = '업로드자'
                        st.session_state.sort_ascending = True
                    st.rerun()
            with col6:
                st.markdown("**AI검색**")
            with col7:
                st.markdown("**작업**")
            
            st.markdown("---")
            
            # 정렬 처리
            if st.session_state.sort_column == '파일명':
                table_data.sort(key=lambda x: x['파일명'], reverse=not st.session_state.sort_ascending)
            elif st.session_state.sort_column == '크기':
                table_data.sort(key=lambda x: x['파일크기원본'], reverse=not st.session_state.sort_ascending)
            elif st.session_state.sort_column == '업로드일':
                table_data.sort(key=lambda x: x['업로드일'], reverse=not st.session_state.sort_ascending)
            elif st.session_state.sort_column == '업로드자':
                table_data.sort(key=lambda x: x['업로드자'], reverse=not st.session_state.sort_ascending)
            
            # 개별 파일 행 표시 (버튼 포함)
            for i, doc in enumerate(table_data):
                with st.container():
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 3, 1, 1.5, 1, 1, 1.5])
                    
                    with col1:
                        st.write(doc['타입'])
                    with col2:
                        st.write(doc['파일명'])
                    with col3:
                        st.write(doc['크기'])
                    with col4:
                        st.write(doc['업로드일'])
                    with col5:
                        st.write(doc['업로드자'])
                    with col6:
                        st.write(doc['AI검색'])
                    with col7:
                        # 개별 파일 작업 버튼
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            # 다운로드 버튼
                            if os.path.exists(doc['파일경로']):
                                try:
                                    with open(doc['파일경로'], 'rb') as f:
                                        st.download_button(
                                            label="📥",
                                            data=f.read(),
                                            file_name=doc['파일명'],
                                            mime="application/octet-stream",
                                            key=f"download_{doc['ID']}",
                                            help="다운로드"
                                        )
                                except Exception as e:
                                    st.button("📥", disabled=True, key=f"download_disabled_{doc['ID']}")
                            else:
                                st.button("📥", disabled=True, key=f"download_missing_{doc['ID']}")
                        
                        with col_btn2:
                            # 삭제 버튼
                            if st.button("🗑️", key=f"delete_{doc['ID']}", help="삭제"):
                                if st.session_state.get(f"confirm_delete_{doc['ID']}", False):
                                    # 실제 삭제 실행
                                    try:
                                        # 데이터베이스에서 삭제
                                        db.delete_document(doc['ID'])
                                        
                                        # 실제 파일 삭제
                                        if os.path.exists(doc['파일경로']):
                                            os.remove(doc['파일경로'])
                                        
                                        st.success(f"'{doc['파일명']}' 파일이 삭제되었습니다.")
                                        st.session_state[f"confirm_delete_{doc['ID']}"] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"파일 삭제 중 오류: {str(e)}")
                                else:
                                    st.session_state[f"confirm_delete_{doc['ID']}"] = True
                                    st.warning("⚠️ 삭제 확인을 위해 다시 클릭해주세요.")
                    
                    # 행 구분선
                    if i < len(table_data) - 1:
                        st.divider()
            
        else:
            st.info("아직 업로드된 강의자료가 없습니다.")
    
    except Exception as e:
        st.error(f"강의자료 목록을 불러오는 중 오류가 발생했습니다: {str(e)}")
        
        # 세션 데이터 백업으로 표시
        session_materials = st.session_state.get('course_materials', {}).get(course_id, [])
        if session_materials:
            st.markdown("##### 세션 데이터 (백업)")
            for material in session_materials:
                with st.container():
                    col1, col2, col3 = st.columns([4, 2, 1])
                    
                    with col1:
                        st.write(f"📄 **{material['name']}**")
                        st.caption(f"업로드: {material['uploaded_at']}")
                    
                    with col2:
                        file_size_kb = material['size'] / 1024
                        st.write(f"크기: {file_size_kb:.1f} KB")
                    
                    with col3:
                        if st.button("🗑️", key=f"delete_session_{material['id']}", help="삭제"):
                            st.session_state.course_materials[course_id].remove(material)
                            st.rerun()

def show_course_materials_view(course_id: str, course: dict):
    """강의자료 보기 (학생용)"""
    st.markdown("### 📚 강의자료")
    
    # 데이터베이스에서 강의자료 목록 가져오기
    try:
        from database.models import DatabaseManager
        import pandas as pd
        import os
        
        db = DatabaseManager()
        documents = db.get_course_documents(course_id)
        
        if documents:
            st.markdown(f"##### 총 {len(documents)}개의 강의자료")
            
            # 정렬 상태 초기화 (학생용)
            if 'sort_column_student' not in st.session_state:
                st.session_state.sort_column_student = '업로드일'
            if 'sort_ascending_student' not in st.session_state:
                st.session_state.sort_ascending_student = False
            
            # 문서 데이터 처리
            table_data = []
            for doc in documents:
                # 파일 타입에 따른 아이콘 설정
                file_type = doc.get('file_type', '').lower()
                if 'pdf' in file_type:
                    icon = "📄"
                elif 'word' in file_type or 'docx' in file_type:
                    icon = "📝"
                elif 'excel' in file_type or 'xlsx' in file_type:
                    icon = "📊"
                elif 'powerpoint' in file_type or 'pptx' in file_type:
                    icon = "📊"
                elif 'image' in file_type:
                    icon = "🖼️"
                else:
                    icon = "📄"
                
                # 파일 크기 계산
                file_size_kb = doc['file_size'] / 1024
                if file_size_kb < 1024:
                    size_str = f"{file_size_kb:.1f} KB"
                else:
                    size_str = f"{file_size_kb/1024:.1f} MB"
                
                # 벡터화 상태
                ai_status = "🔍 가능" if doc.get('is_vectorized', False) else "⏳ 처리중"
                
                table_data.append({
                    'ID': doc['id'],
                    '타입': icon,
                    '파일명': doc['original_filename'],
                    '크기': size_str,
                    '업로드일': doc['uploaded_at'][:16],  # 날짜만 표시
                    '업로드자': doc['uploader_name'],
                    'AI검색': ai_status,
                    '파일경로': doc['file_path'],
                    '파일크기원본': doc['file_size']
                })
            
            # 파일 헤더 (학생용 - 정렬 버튼 포함)
            st.markdown("---")
            
            col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 3, 1, 1.5, 1, 1, 1])
            with col1:
                st.markdown("**타입**")
            with col2:
                if st.button("**파일명** ↕️", key="sort_filename_student", help="파일명으로 정렬"):
                    if st.session_state.sort_column_student == '파일명':
                        st.session_state.sort_ascending_student = not st.session_state.sort_ascending_student
                    else:
                        st.session_state.sort_column_student = '파일명'
                        st.session_state.sort_ascending_student = True
                    st.rerun()
            with col3:
                if st.button("**크기** ↕️", key="sort_size_student", help="크기로 정렬"):
                    if st.session_state.sort_column_student == '크기':
                        st.session_state.sort_ascending_student = not st.session_state.sort_ascending_student
                    else:
                        st.session_state.sort_column_student = '크기'
                        st.session_state.sort_ascending_student = True
                    st.rerun()
            with col4:
                if st.button("**업로드일** ↕️", key="sort_date_student", help="업로드일로 정렬"):
                    if st.session_state.sort_column_student == '업로드일':
                        st.session_state.sort_ascending_student = not st.session_state.sort_ascending_student
                    else:
                        st.session_state.sort_column_student = '업로드일'
                        st.session_state.sort_ascending_student = True
                    st.rerun()
            with col5:
                if st.button("**업로드자** ↕️", key="sort_uploader_student", help="업로드자로 정렬"):
                    if st.session_state.sort_column_student == '업로드자':
                        st.session_state.sort_ascending_student = not st.session_state.sort_ascending_student
                    else:
                        st.session_state.sort_column_student = '업로드자'
                        st.session_state.sort_ascending_student = True
                    st.rerun()
            with col6:
                st.markdown("**AI검색**")
            with col7:
                st.markdown("**다운로드**")
            
            st.markdown("---")
            
            # 정렬 처리 (학생용)
            if st.session_state.sort_column_student == '파일명':
                table_data.sort(key=lambda x: x['파일명'], reverse=not st.session_state.sort_ascending_student)
            elif st.session_state.sort_column_student == '크기':
                table_data.sort(key=lambda x: x['파일크기원본'], reverse=not st.session_state.sort_ascending_student)
            elif st.session_state.sort_column_student == '업로드일':
                table_data.sort(key=lambda x: x['업로드일'], reverse=not st.session_state.sort_ascending_student)
            elif st.session_state.sort_column_student == '업로드자':
                table_data.sort(key=lambda x: x['업로드자'], reverse=not st.session_state.sort_ascending_student)
            
            # 개별 파일 행 표시 (학생용)
            for i, doc in enumerate(table_data):
                with st.container():
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 3, 1, 1.5, 1, 1, 1])
                    
                    with col1:
                        st.write(doc['타입'])
                    with col2:
                        st.write(doc['파일명'])
                    with col3:
                        st.write(doc['크기'])
                    with col4:
                        st.write(doc['업로드일'])
                    with col5:
                        st.write(doc['업로드자'])
                    with col6:
                        st.write(doc['AI검색'])
                    with col7:
                        # 다운로드 버튼
                        if os.path.exists(doc['파일경로']):
                            try:
                                with open(doc['파일경로'], 'rb') as f:
                                    st.download_button(
                                        label="📥",
                                        data=f.read(),
                                        file_name=doc['파일명'],
                                        mime="application/octet-stream",
                                        key=f"download_student_{doc['ID']}",
                                        help="다운로드"
                                    )
                            except Exception as e:
                                st.button("📥", disabled=True, key=f"download_student_disabled_{doc['ID']}")
                        else:
                            st.button("📥", disabled=True, key=f"download_student_missing_{doc['ID']}")
                    
                    # 행 구분선
                    if i < len(table_data) - 1:
                        st.divider()
            
            # 일괄 다운로드 섹션 (학생용)
            st.markdown("#### 📥 일괄 다운로드")
            
            # 파일 선택 (학생용)
            if table_data:
                selected_files = st.multiselect(
                    "다운로드할 파일 선택:",
                    options=[f"{doc['타입']} {doc['파일명']}" for doc in table_data],
                    key="selected_files_student"
                )
                
                if selected_files:
                    if st.button("📥 선택한 파일 다운로드", key="download_selected_student"):
                        for file_display in selected_files:
                            # 선택된 파일 찾기
                            file_name = file_display.split(" ", 1)[1]  # 아이콘 제거
                            selected_doc = next((doc for doc in table_data if doc['파일명'] == file_name), None)
                            
                            if selected_doc and os.path.exists(selected_doc['파일경로']):
                                try:
                                    with open(selected_doc['파일경로'], 'rb') as f:
                                        st.download_button(
                                            label=f"📥 {selected_doc['파일명']}",
                                            data=f.read(),
                                            file_name=selected_doc['파일명'],
                                            mime="application/octet-stream",
                                            key=f"download_student_multi_{selected_doc['ID']}"
                                        )
                                except Exception as e:
                                    st.error(f"{selected_doc['파일명']} 다운로드 중 오류: {str(e)}")
        else:
            st.info("아직 업로드된 강의자료가 없습니다.")
    
    except Exception as e:
        st.error(f"강의자료 목록을 불러오는 중 오류가 발생했습니다: {str(e)}")
        
        # 세션 데이터 백업으로 표시
        materials = st.session_state.get('course_materials', {}).get(course_id, [])
        if materials:
            st.markdown("##### 세션 데이터 (백업)")
            for material in materials:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.write(f"📄 **{material['name']}**")
                        st.caption(f"업로드: {material['uploaded_at']} | 크기: {material['size']/1024:.1f} KB")
                    
                    with col2:
                        st.button("📥 다운로드", key=f"download_backup_{material['id']}")
                    
                    st.markdown("---")

def show_classroom_ai_search(course_id: str, course: dict):
    """강의실 AI 검색"""
    st.markdown("### 🔍 AI 검색")
    st.info("이 기능은 현재 강의의 업로드된 자료에서만 검색됩니다.")
    
    # 검색 UI는 기존 AI 검색 페이지와 유사하지만 현재 강의로 제한
    search_query = st.text_input("검색어를 입력하세요:", placeholder="예: 머신러닝의 정의")
    
    if search_query:
        st.write(f"'{course['name']}' 강의 자료에서 검색 중...")
        # TODO: 실제 검색 로직은 AI 기능 구현 시 추가
        st.info("AI 검색 기능은 곧 추가될 예정입니다.")

def show_classroom_chat(course_id: str, course: dict):
    """강의실 채팅"""
    st.markdown("### 💬 강의실 채팅")
    st.info(f"'{course['name']}' 강의실 전용 채팅방입니다.")
    
    # TODO: 실제 채팅 기능 구현
    st.info("채팅 기능은 곧 추가될 예정입니다.")

def show_course_analytics(course_id: str, course: dict):
    """수업 분석 (교수자용)"""
    st.markdown("### 📈 수업 분석")
    st.info("수강생들의 학습 패턴과 참여도를 분석합니다.")
    
    # TODO: 분석 기능 구현
    st.info("분석 기능은 곧 추가될 예정입니다.")

def show_student_notes(course_id: str, course: dict):
    """학습노트 (학생용)"""
    st.markdown("### 📝 학습노트")
    st.info(f"'{course['name']}' 강의 전용 학습노트입니다.")
    
    # TODO: 노트 기능 구현
    st.info("학습노트 기능은 곧 추가될 예정입니다.")

def show_classroom_settings(course_id: str, course: dict):
    """강의실 도구 설정"""
    st.markdown("### ⚙️ 강의실 도구 설정")
    
    # 탭으로 설정 구분
    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 AI 도구 설정", 
        "📊 분석 설정", 
        "💬 채팅 설정", 
        "🔔 알림 설정"
    ])
    
    with tab1:
        show_ai_tool_settings(course_id, course)
    
    with tab2:
        show_analytics_settings(course_id, course)
    
    with tab3:
        show_chat_settings(course_id, course)
    
    with tab4:
        show_notification_settings_classroom(course_id, course)

def show_ai_tool_settings(course_id: str, course: dict):
    """AI 도구 설정"""
    st.markdown("#### 🤖 AI 도구 설정")
    
    # AI 모델 설정
    st.markdown("**🧠 AI 모델 설정**")
    
    ai_model = st.selectbox(
        "AI 모델 선택",
        ["GPT-4", "GPT-3.5", "Claude", "Gemini"],
        index=0
    )
    
    response_style = st.selectbox(
        "응답 스타일",
        ["학술적", "친근한", "간결한", "상세한"],
        index=0
    )
    
    difficulty_level = st.select_slider(
        "응답 난이도",
        options=["초급", "중급", "고급", "전문가"],
        value="중급"
    )
    
    # 검색 설정
    st.markdown("**🔍 검색 설정**")
    
    search_scope = st.multiselect(
        "검색 범위",
        ["강의자료", "교과서", "참고문헌", "온라인 자료"],
        default=["강의자료"]
    )
    
    max_results = st.slider("최대 검색 결과 수", 5, 50, 20)
    
    # 자동 기능 설정
    st.markdown("**🔄 자동 기능**")
    
    auto_summarize = st.checkbox("자동 요약 생성", value=True)
    auto_keywords = st.checkbox("자동 키워드 추출", value=True)
    auto_quiz = st.checkbox("자동 퀴즈 생성", value=False)
    
    if st.button("💾 AI 도구 설정 저장"):
        st.success("AI 도구 설정이 저장되었습니다!")

def show_analytics_settings(course_id: str, course: dict):
    """분석 설정"""
    st.markdown("#### 📊 분석 설정")
    
    # 분석 데이터 수집
    st.markdown("**📈 데이터 수집**")
    
    collect_participation = st.checkbox("참여도 데이터 수집", value=True)
    collect_performance = st.checkbox("성과 데이터 수집", value=True)
    collect_engagement = st.checkbox("참여 패턴 분석", value=True)
    
    # 리포트 생성
    st.markdown("**📄 리포트 생성**")
    
    report_frequency = st.selectbox(
        "리포트 생성 주기",
        ["매일", "매주", "매월", "학기말"],
        index=1
    )
    
    include_student_analytics = st.checkbox("학생 개별 분석 포함", value=True)
    include_class_comparison = st.checkbox("클래스 비교 분석", value=False)
    
    # 알림 설정
    st.markdown("**🔔 분석 알림**")
    
    alert_low_participation = st.checkbox("참여도 저하 알림", value=True)
    alert_difficult_topics = st.checkbox("어려운 주제 알림", value=True)
    
    if st.button("💾 분석 설정 저장"):
        st.success("분석 설정이 저장되었습니다!")

def show_chat_settings(course_id: str, course: dict):
    """채팅 설정"""
    st.markdown("#### 💬 채팅 설정")
    
    # 채팅 기본 설정
    st.markdown("**💬 채팅 기본 설정**")
    
    enable_chat = st.checkbox("채팅 활성화", value=True)
    enable_file_sharing = st.checkbox("파일 공유 허용", value=True)
    enable_private_messages = st.checkbox("개인 메시지 허용", value=False)
    
    # 모더레이션 설정
    st.markdown("**🛡️ 모더레이션**")
    
    auto_moderation = st.checkbox("자동 모더레이션", value=True)
    word_filter = st.checkbox("부적절한 언어 필터", value=True)
    
    # 메시지 설정
    max_message_length = st.slider("최대 메시지 길이", 100, 1000, 500)
    message_history_days = st.slider("메시지 보관 기간 (일)", 7, 365, 30)
    
    if st.button("💾 채팅 설정 저장"):
        st.success("채팅 설정이 저장되었습니다!")

def show_notification_settings_classroom(course_id: str, course: dict):
    """알림 설정"""
    st.markdown("#### 🔔 알림 설정")
    
    # 알림 유형
    st.markdown("**📱 알림 유형**")
    
    email_notifications = st.checkbox("이메일 알림", value=True)
    push_notifications = st.checkbox("푸시 알림", value=True)
    
    # 알림 이벤트
    st.markdown("**⚡ 알림 이벤트**")
    
    notify_new_student = st.checkbox("새 학생 수강신청", value=True)
    notify_new_question = st.checkbox("새 질문 등록", value=True)
    notify_assignment_submit = st.checkbox("과제 제출", value=True)
    notify_low_participation = st.checkbox("참여도 저하", value=True)
    
    # 알림 스케줄
    st.markdown("**⏰ 알림 스케줄**")
    
    daily_summary = st.checkbox("일일 요약 보고서", value=True)
    weekly_report = st.checkbox("주간 리포트", value=True)
    
    summary_time = st.time_input("요약 보고서 발송 시간", value=None)
    
    if st.button("💾 알림 설정 저장"):
        st.success("알림 설정이 저장되었습니다!")

def show_course_settings(course_id: str, course: dict):
    """강의 설정 편집"""
    st.markdown("### ⚙️ 강의 설정")
    
    # 데이터베이스 매니저 초기화
    if 'db_manager' not in st.session_state:
        from database.models import DatabaseManager
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    
    # 현재 강의 정보 불러오기
    current_course = db_manager.get_course_by_id(course_id)
    
    if not current_course:
        st.error("강의 정보를 불러올 수 없습니다.")
        return
    
    st.markdown("#### 🔧 기본 정보 편집")
    
    # 강의 기본 정보 편집 폼
    with st.form("course_settings_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # 강의명
            course_name = st.text_input(
                "강의명",
                value=current_course.get('name', ''),
                placeholder="강의명을 입력하세요"
            )
            
            # 학과
            department = st.text_input(
                "개설학과",
                value=current_course.get('department', ''),
                placeholder="학과명을 입력하세요"
            )
            
            # 학점
            credit = st.number_input(
                "학점",
                min_value=1,
                max_value=9,
                value=current_course.get('credit', 3),
                step=1
            )
        
        with col2:
            # 학기
            semester = st.text_input(
                "학기",
                value=current_course.get('semester', ''),
                placeholder="예: 2024-1"
            )
            
            # 최대 수강인원
            max_students = st.number_input(
                "최대 수강인원",
                min_value=1,
                max_value=500,
                value=current_course.get('max_students', 30),
                step=1
            )
            
            # 강의 상태
            is_active = st.checkbox(
                "강의 활성화",
                value=current_course.get('is_active', True)
            )
        
        # 강의 설명
        description = st.text_area(
            "강의 설명",
            value=current_course.get('description', ''),
            placeholder="강의에 대한 설명을 입력하세요...",
            height=100
        )
        
        # 저장 버튼
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 설정 저장", type="primary")
        with col2:
            reset = st.form_submit_button("🔄 초기화")
    
    # 폼 제출 처리
    if submitted:
        # 변경사항 확인
        changes = {}
        
        if course_name != current_course.get('name'):
            changes['name'] = course_name
        if department != current_course.get('department'):
            changes['department'] = department
        if credit != current_course.get('credit'):
            changes['credit'] = credit
        if semester != current_course.get('semester'):
            changes['semester'] = semester
        if max_students != current_course.get('max_students'):
            changes['max_students'] = max_students
        if is_active != current_course.get('is_active'):
            changes['is_active'] = is_active
        if description != current_course.get('description'):
            changes['description'] = description
        
        if changes:
            # 데이터베이스 업데이트
            success = db_manager.update_course_info(course_id, **changes)
            
            if success:
                st.success("✅ 강의 설정이 성공적으로 저장되었습니다!")
                
                # 세션 상태에서 강의 정보 업데이트
                if 'current_course' in st.session_state:
                    st.session_state.current_course.update(changes)
                
                # 1초 후 페이지 새로고침
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ 설정 저장 중 오류가 발생했습니다.")
        else:
            st.info("변경사항이 없습니다.")
    
    if reset:
        st.rerun()
    
    # 강의 통계 정보
    st.markdown("#### 📊 강의 통계")
    
    # 통계 데이터 수집
    enrollments = db_manager.get_course_enrollments(course_id)
    documents = db_manager.get_course_documents(course_id)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("현재 수강생", len(enrollments))
    with col2:
        st.metric("최대 수강생", current_course.get('max_students', 0))
    with col3:
        st.metric("강의자료", len(documents))
    with col4:
        capacity_rate = (len(enrollments) / current_course.get('max_students', 1)) * 100
        st.metric("수강률", f"{capacity_rate:.1f}%")
    
    # 위험 구역
    st.markdown("#### ⚠️ 위험 구역")
    
    with st.expander("🚨 강의 완전 삭제"):
        st.warning("⚠️ 이 작업은 되돌릴 수 없습니다!")
        st.write("강의를 삭제하면 다음 데이터가 모두 제거됩니다:")
        st.write("- 강의 정보")
        st.write("- 수강신청 기록")
        st.write("- 강의자료")
        st.write("- 검색 기록")
        
        delete_confirm = st.text_input(
            "삭제를 확인하려면 '강의 삭제 확인'을 입력하세요:",
            placeholder="강의 삭제 확인"
        )
        
        if st.button("🗑️ 강의 완전 삭제", type="secondary"):
            if delete_confirm == "강의 삭제 확인":
                # TODO: 강의 완전 삭제 로직 구현
                st.error("강의 삭제 기능은 안전을 위해 현재 비활성화되어 있습니다.")
            else:
                st.error("삭제 확인 문구를 정확히 입력해주세요.")

if __name__ == "__main__":
    show_classroom() 