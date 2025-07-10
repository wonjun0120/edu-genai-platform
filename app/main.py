import streamlit as st
import sys
from pathlib import Path

# 현재 파일의 부모 디렉토리를 시스템 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 분리된 모듈들 import
from utils.session_utils import init_session_state, get_user_role
from components.header import show_header
from components.navigation import get_student_menu, get_instructor_menu, get_admin_menu
from pages.auth import show_role_selection
from pages.home import show_student_home, show_instructor_home, show_admin_home
from pages.chat import show_chat_page
from pages.file_manager import show_file_manager
from pages.analytics import show_analytics_page
from pages.settings import show_settings_page
from pages.courses import show_instructor_courses, show_student_courses
from pages.ai_search import show_ai_search_page
from pages.document_upload import show_document_upload
from pages.classroom import show_classroom

# 페이지 설정
st.set_page_config(
    page_title="DX·AI 교육 플랫폼",
    page_icon="🎓",
    layout="wide"
)

# 사이드바 완전히 숨기기
st.markdown("""
<style>
    /* 사이드바 완전히 숨기기 */
    .css-1d391kg {
        display: none !important;
    }
    .css-1rs6os {
        display: none !important;
    }
    .css-17eq0hr {
        display: none !important;
    }
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    .css-1lcbmhc {
        display: none !important;
    }
    .css-1outpf7 {
        display: none !important;
    }
    /* 새로운 Streamlit 버전용 선택자 */
    .st-emotion-cache-10oheav {
        display: none !important;
    }
    .st-emotion-cache-1y4p8pa {
        display: none !important;
    }
    .st-emotion-cache-6qob1r {
        display: none !important;
    }
    [data-testid="stSidebar"] {
        display: none !important;
    }
    /* 전체 레이아웃에서 사이드바 공간 제거 */
    .main .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: none !important;
    }
    .stApp > div:first-child {
        margin-left: 0px !important;
    }
</style>
""", unsafe_allow_html=True)

# 사이드바 내용도 비우기
with st.sidebar:
    st.empty()

# 학습자 대시보드
def show_student_dashboard():
    """학습자 대시보드"""
    st.markdown("## 📚 학습자 대시보드")
    
    # 메뉴 선택
    selected = get_student_menu()
    
    if selected == "🏠 홈":
        show_student_home()
    elif selected == "📚 내 강의":
        show_student_courses()
    elif selected == "🏛️ 강의실":
        show_classroom()
    elif selected == "📝 학습노트":
        show_notes_page()
    elif selected == "🎨 AI도구":
        show_ai_tools()

# 교수자 대시보드
def show_instructor_dashboard():
    """교수자 대시보드"""
    st.markdown("## 👨‍🏫 교수자 대시보드")
    
    # 메뉴 선택
    selected = get_instructor_menu()
    
    if selected == "🏠 홈":
        show_instructor_home()
    elif selected == "📚 강의 관리":
        show_instructor_courses()
    elif selected == "🏛️ 강의실":
        show_classroom()
    elif selected == "📊 수업분석":
        show_analytics_page()

# 관리자 대시보드
def show_admin_dashboard():
    """관리자 대시보드"""
    st.markdown("## 🛠️ 관리자 대시보드")
    
    # 메뉴 선택
    selected = get_admin_menu()
    
    if selected == "🏠 홈":
        show_admin_home()
    elif selected == "📊 시스템현황":
        show_system_status()
    elif selected == "👥 사용자관리":
        show_user_management()
    elif selected == "📈 통계분석":
        show_analytics_page()
    elif selected == "⚙️ 시스템설정":
        show_settings_page()

# 아직 구현되지 않은 페이지들
def show_notes_page():
    """학습 노트 페이지"""
    st.markdown("### 📝 학습 노트")
    st.info("학습 노트 기능은 Phase 2에서 구현 예정입니다.")

def show_ai_tools():
    """AI 도구 페이지"""
    st.markdown("### 🎨 AI 도구")
    st.info("AI 도구 기능은 Phase 2에서 구현 예정입니다.")

def show_system_status():
    """시스템 상태 페이지"""
    st.markdown("### 📊 시스템 상태")
    st.info("시스템 상태 모니터링은 Phase 2에서 구현 예정입니다.")

def show_user_management():
    """사용자 관리 페이지"""
    st.markdown("### 👥 사용자 관리")
    st.info("사용자 관리 기능은 Phase 2에서 구현 예정입니다.")

# 메인 앱 실행
def show_main_app(user_role):
    """역할별 메인 앱 표시"""
    show_header()
    
    if user_role == "student":
        show_student_dashboard()
    elif user_role == "instructor":
        show_instructor_dashboard()
    elif user_role == "admin":
        show_admin_dashboard()

# 메인 실행
def main():
    """메인 함수"""
    init_session_state()
    
    user_role = get_user_role()
    
    if user_role is None:
        show_role_selection()
    else:
        show_main_app(user_role)

if __name__ == "__main__":
    main()
