import streamlit as st
from utils.session_utils import get_user_role, get_user_name

def show_settings_page():
    """설정 페이지"""
    st.markdown("### ⚙️ 설정")
    
    user_role = get_user_role()
    
    # 역할별 설정 메뉴
    if user_role == "student":
        show_student_settings()
    elif user_role == "instructor":
        show_instructor_settings()
    elif user_role == "admin":
        show_admin_settings()

def show_student_settings():
    """학습자 설정"""
    st.markdown("#### 👨‍🎓 학습자 설정")
    
    # 탭으로 구분
    tabs = st.tabs(["🎯 학습 설정", "🔔 알림 설정", "🎨 화면 설정", "📊 데이터 관리"])
    
    with tabs[0]:
        show_learning_settings()
    
    with tabs[1]:
        show_notification_settings()
    
    with tabs[2]:
        show_display_settings()
    
    with tabs[3]:
        show_data_management()

def show_instructor_settings():
    """교수자 설정"""
    st.markdown("#### 👨‍🏫 교수자 설정")
    
    # 탭으로 구분
    tabs = st.tabs(["🏫 수업 설정", "🤖 AI 설정", "👥 학생 관리", "📊 평가 설정", "🔔 알림 설정"])
    
    with tabs[0]:
        show_class_settings()
    
    with tabs[1]:
        show_ai_settings()
    
    with tabs[2]:
        show_student_management_settings()
    
    with tabs[3]:
        show_evaluation_settings()
    
    with tabs[4]:
        show_notification_settings()

def show_admin_settings():
    """관리자 설정"""
    st.markdown("#### 🛠️ 관리자 설정")
    
    # 탭으로 구분
    tabs = st.tabs(["🖥️ 시스템 설정", "👥 사용자 관리", "🔐 보안 설정", "📊 모니터링", "💾 백업 설정"])
    
    with tabs[0]:
        show_system_settings()
    
    with tabs[1]:
        show_user_management_settings()
    
    with tabs[2]:
        show_security_settings()
    
    with tabs[3]:
        show_monitoring_settings()
    
    with tabs[4]:
        show_backup_settings()

def show_learning_settings():
    """학습 설정"""
    st.markdown("##### 🎯 학습 설정")
    
    # 학습 목표 설정
    st.markdown("**📚 학습 목표**")
    daily_goal = st.slider("일일 학습 목표 (시간)", 1, 8, 3)
    weekly_goal = st.slider("주간 학습 목표 (시간)", 5, 40, 20)
    
    # 난이도 설정
    st.markdown("**🎯 선호 난이도**")
    difficulty = st.select_slider(
        "AI 답변 난이도 설정",
        options=["초급", "중급", "고급", "전문가"],
        value="중급"
    )
    
    # 학습 주제 관심도
    st.markdown("**📖 관심 주제**")
    topics = st.multiselect(
        "관심 있는 학습 주제를 선택하세요:",
        ["Python", "JavaScript", "데이터 구조", "알고리즘", "웹 개발", "머신러닝", "데이터베이스", "네트워크"],
        default=["Python", "데이터 구조"]
    )
    
    if st.button("💾 학습 설정 저장"):
        st.success("학습 설정이 저장되었습니다!")

def show_notification_settings():
    """알림 설정"""
    st.markdown("##### 🔔 알림 설정")
    
    # 알림 유형별 설정
    st.markdown("**📱 알림 유형**")
    
    email_notifications = st.checkbox("이메일 알림", value=True)
    browser_notifications = st.checkbox("브라우저 알림", value=True)
    daily_summary = st.checkbox("일일 학습 요약", value=False)
    
    # 알림 시간 설정
    st.markdown("**⏰ 알림 시간**")
    reminder_time = st.time_input("학습 알림 시간", value=None)
    
    # 알림 빈도
    reminder_frequency = st.selectbox(
        "알림 빈도",
        ["매일", "주 3회", "주 2회", "주 1회", "알림 없음"]
    )
    
    if st.button("🔔 알림 설정 저장"):
        st.success("알림 설정이 저장되었습니다!")

def show_display_settings():
    """화면 설정"""
    st.markdown("##### 🎨 화면 설정")
    
    # 테마 설정
    st.markdown("**🎨 테마**")
    theme = st.selectbox("테마 선택", ["라이트 모드", "다크 모드", "시스템 기본값"])
    
    # 폰트 크기
    font_size = st.slider("폰트 크기", 12, 20, 14)
    
    # 언어 설정
    language = st.selectbox("언어", ["한국어", "English", "日本語"])
    
    # 채팅 표시 설정
    st.markdown("**💬 채팅 표시**")
    show_timestamps = st.checkbox("시간 표시", value=True)
    show_avatars = st.checkbox("프로필 아바타 표시", value=True)
    max_messages = st.slider("최대 메시지 표시 수", 10, 100, 50)
    
    if st.button("🎨 화면 설정 저장"):
        st.success("화면 설정이 저장되었습니다!")

def show_data_management():
    """데이터 관리"""
    st.markdown("##### 📊 데이터 관리")
    
    # 데이터 사용량
    st.markdown("**📈 데이터 사용량**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("채팅 데이터", "2.3 MB")
        st.metric("업로드 파일", "15.7 MB")
    
    with col2:
        st.metric("학습 기록", "1.2 MB")
        st.metric("총 사용량", "19.2 MB")
    
    # 데이터 관리 옵션
    st.markdown("**🗂️ 데이터 관리**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 데이터 백업", use_container_width=True):
            st.info("데이터 백업 기능은 Phase 2에서 구현 예정입니다.")
    
    with col2:
        if st.button("🗑️ 데이터 삭제", use_container_width=True):
            st.warning("데이터 삭제 기능은 Phase 2에서 구현 예정입니다.")

def show_class_settings():
    """수업 설정"""
    st.markdown("##### 🏫 수업 설정")
    
    # 수업 정보
    st.markdown("**📚 수업 정보**")
    
    class_name = st.text_input("수업명", value="파이썬 프로그래밍")
    class_code = st.text_input("수업 코드", value="CS101")
    semester = st.selectbox("학기", ["2024-1", "2024-2", "2024-여름", "2024-겨울"])
    
    # 수업 설정
    max_students = st.number_input("최대 수강 인원", min_value=1, max_value=100, value=30)
    
    # 과제 설정
    st.markdown("**📝 과제 설정**")
    
    assignment_submission = st.checkbox("과제 제출 허용", value=True)
    late_submission = st.checkbox("늦은 제출 허용", value=True)
    
    if late_submission:
        late_penalty = st.slider("늦은 제출 벌점 (%)", 0, 50, 10)
    
    if st.button("🏫 수업 설정 저장"):
        st.success("수업 설정이 저장되었습니다!")

def show_ai_settings():
    """AI 설정"""
    st.markdown("##### 🤖 AI 설정")
    
    # AI 모델 설정
    st.markdown("**🧠 AI 모델**")
    ai_model = st.selectbox("AI 모델", ["GPT-4", "GPT-3.5", "Claude", "Gemini"])
    
    # 응답 스타일 설정
    response_style = st.selectbox(
        "응답 스타일",
        ["친근한 교사", "전문적인 조교", "엄격한 교수", "격려하는 멘토"]
    )
    
    # 프롬프트 템플릿
    st.markdown("**📝 프롬프트 템플릿**")
    
    system_prompt = st.text_area(
        "시스템 프롬프트",
        value="당신은 도움이 되는 교육 어시스턴트입니다. 학생들의 학습을 돕고 격려해주세요.",
        height=100
    )
    
    # AI 응답 설정
    st.markdown("**⚙️ 응답 설정**")
    
    max_tokens = st.slider("최대 토큰 수", 100, 2000, 500)
    temperature = st.slider("창의성 (Temperature)", 0.0, 2.0, 0.7)
    
    if st.button("🤖 AI 설정 저장"):
        st.success("AI 설정이 저장되었습니다!")

def show_student_management_settings():
    """학생 관리 설정"""
    st.markdown("##### 👥 학생 관리 설정")
    
    # 학생 등록 설정
    st.markdown("**📝 학생 등록**")
    
    auto_enrollment = st.checkbox("자동 등록 허용", value=True)
    require_approval = st.checkbox("승인 필요", value=False)
    
    # 학생 권한 설정
    st.markdown("**🔐 학생 권한**")
    
    can_upload_files = st.checkbox("파일 업로드 허용", value=True)
    can_create_groups = st.checkbox("그룹 생성 허용", value=False)
    can_share_notes = st.checkbox("노트 공유 허용", value=True)
    
    if st.button("👥 학생 관리 설정 저장"):
        st.success("학생 관리 설정이 저장되었습니다!")

def show_evaluation_settings():
    """평가 설정"""
    st.markdown("##### 📊 평가 설정")
    
    # 평가 방식
    st.markdown("**📈 평가 방식**")
    
    grading_scale = st.selectbox("채점 기준", ["A-F", "100점 만점", "Pass/Fail"])
    
    # 가중치 설정
    st.markdown("**⚖️ 가중치 설정**")
    
    participation_weight = st.slider("참여도 (%)", 0, 50, 20)
    assignment_weight = st.slider("과제 (%)", 0, 70, 40)
    exam_weight = st.slider("시험 (%)", 0, 70, 40)
    
    # 총합 검증
    total_weight = participation_weight + assignment_weight + exam_weight
    if total_weight != 100:
        st.error(f"가중치 합계가 {total_weight}%입니다. 100%가 되도록 조정해주세요.")
    
    if st.button("📊 평가 설정 저장"):
        if total_weight == 100:
            st.success("평가 설정이 저장되었습니다!")
        else:
            st.error("가중치 합계를 100%로 맞춰주세요.")

def show_system_settings():
    """시스템 설정"""
    st.markdown("##### 🖥️ 시스템 설정")
    
    # 시스템 정보
    st.markdown("**ℹ️ 시스템 정보**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**버전:** v1.0.0")
        st.info("**빌드:** 2024.01.15")
    
    with col2:
        st.info("**서버:** 정상 운영")
        st.info("**DB:** 연결됨")
    
    # 시스템 설정
    st.markdown("**⚙️ 시스템 설정**")
    
    max_upload_size = st.slider("최대 업로드 크기 (MB)", 1, 100, 10)
    session_timeout = st.slider("세션 타임아웃 (분)", 10, 240, 60)
    
    # 캐시 설정
    st.markdown("**💾 캐시 설정**")
    
    enable_caching = st.checkbox("캐시 활성화", value=True)
    cache_duration = st.slider("캐시 유지 시간 (시간)", 1, 24, 6)
    
    if st.button("🖥️ 시스템 설정 저장"):
        st.success("시스템 설정이 저장되었습니다!")

def show_user_management_settings():
    """사용자 관리 설정"""
    st.markdown("##### 👥 사용자 관리 설정")
    
    # 사용자 등록 설정
    st.markdown("**📝 사용자 등록**")
    
    allow_registration = st.checkbox("신규 등록 허용", value=True)
    require_email_verification = st.checkbox("이메일 인증 필요", value=True)
    
    # 권한 설정
    st.markdown("**🔐 기본 권한**")
    
    default_role = st.selectbox("기본 역할", ["학습자", "교수자", "관리자"])
    
    if st.button("👥 사용자 관리 설정 저장"):
        st.success("사용자 관리 설정이 저장되었습니다!")

def show_security_settings():
    """보안 설정"""
    st.markdown("##### 🔐 보안 설정")
    
    # 패스워드 정책
    st.markdown("**🔒 패스워드 정책**")
    
    min_password_length = st.slider("최소 길이", 4, 20, 8)
    require_uppercase = st.checkbox("대문자 포함", value=True)
    require_lowercase = st.checkbox("소문자 포함", value=True)
    require_numbers = st.checkbox("숫자 포함", value=True)
    require_symbols = st.checkbox("특수문자 포함", value=False)
    
    # 접근 제한
    st.markdown("**🚫 접근 제한**")
    
    max_login_attempts = st.slider("최대 로그인 시도 횟수", 3, 10, 5)
    lockout_duration = st.slider("계정 잠금 시간 (분)", 5, 60, 15)
    
    if st.button("🔐 보안 설정 저장"):
        st.success("보안 설정이 저장되었습니다!")

def show_monitoring_settings():
    """모니터링 설정"""
    st.markdown("##### 📊 모니터링 설정")
    
    # 모니터링 옵션
    st.markdown("**📈 모니터링 옵션**")
    
    enable_logging = st.checkbox("로깅 활성화", value=True)
    enable_metrics = st.checkbox("메트릭 수집", value=True)
    enable_alerts = st.checkbox("알림 활성화", value=True)
    
    # 알림 임계값
    st.markdown("**⚠️ 알림 임계값**")
    
    cpu_threshold = st.slider("CPU 사용률 (%)", 50, 95, 80)
    memory_threshold = st.slider("메모리 사용률 (%)", 50, 95, 85)
    disk_threshold = st.slider("디스크 사용률 (%)", 50, 95, 90)
    
    if st.button("📊 모니터링 설정 저장"):
        st.success("모니터링 설정이 저장되었습니다!")

def show_backup_settings():
    """백업 설정"""
    st.markdown("##### 💾 백업 설정")
    
    # 백업 스케줄
    st.markdown("**⏰ 백업 스케줄**")
    
    backup_frequency = st.selectbox("백업 빈도", ["매일", "주간", "월간"])
    backup_time = st.time_input("백업 시간")
    
    # 백업 보관
    st.markdown("**🗂️ 백업 보관**")
    
    retention_days = st.slider("보관 기간 (일)", 7, 365, 30)
    max_backups = st.slider("최대 백업 개수", 3, 20, 10)
    
    # 백업 위치
    backup_location = st.selectbox("백업 위치", ["로컬 서버", "클라우드 스토리지", "외부 서버"])
    
    if st.button("💾 백업 설정 저장"):
        st.success("백업 설정이 저장되었습니다!")
    
    # 수동 백업
    st.markdown("**🔧 수동 백업**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📦 지금 백업", use_container_width=True):
            st.info("백업 기능은 Phase 2에서 구현 예정입니다.")
    
    with col2:
        if st.button("📥 백업 복원", use_container_width=True):
            st.info("복원 기능은 Phase 2에서 구현 예정입니다.") 