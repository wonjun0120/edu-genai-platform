import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# 현재 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from utils.session_utils import get_user_name, get_user_role
from services.document_service import DocumentService

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
        if st.button("🚪 나가기", type="secondary"):
            del st.session_state.current_course
            st.success("🎉 강의실에서 나왔습니다!")
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 강의 현황", 
        "📚 강의자료 관리", 
        "🔍 AI 검색", 
        "💬 강의실 채팅", 
        "📈 수업 분석"
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
            user_id = f"{get_user_name()}_{get_user_role()}"
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            for i, file in enumerate(uploaded_files):
                status_text.text(f"처리 중: {file.name}")
                
                result = service.process_uploaded_file(file, course_id, user_id)
                results.append(result)
                
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                
                if result['success']:
                    st.success(f"✅ {file.name}: 업로드 완료")
                else:
                    st.error(f"❌ {file.name}: {result['error']}")
            
            status_text.text("✅ 모든 파일 처리 완료!")
            
            # 결과 요약
            successful = [r for r in results if r['success']]
            if successful:
                st.info(f"🎉 {len(successful)}개 파일이 성공적으로 업로드되었습니다!")
    
    # 기존 자료 목록
    st.markdown("#### 📋 업로드된 강의자료")
    
    # 세션 데이터의 기존 자료도 표시
    session_materials = st.session_state.get('course_materials', {}).get(course_id, [])
    
    if session_materials:
        st.markdown("##### 기존 업로드 자료 (세션 데이터)")
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
    
    materials = st.session_state.get('course_materials', {}).get(course_id, [])
    
    if materials:
        for material in materials:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.write(f"📄 **{material['name']}**")
                    st.caption(f"업로드: {material['uploaded_at']} | 크기: {material['size']/1024:.1f} KB")
                
                with col2:
                    st.button("📥 다운로드", key=f"download_{material['id']}")
                
                st.markdown("---")
    else:
        st.info("아직 업로드된 강의자료가 없습니다.")

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

if __name__ == "__main__":
    show_classroom() 