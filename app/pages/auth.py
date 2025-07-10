import streamlit as st
from utils.session_utils import set_user_role, set_user_name

def show_role_selection():
    """역할 선택 페이지"""
    st.markdown("""                
    <div style="text-align: center; padding: 2rem 0;">
    <h1>
        🎓 DX·AI 교육 플랫폼
        <span style="
        font-size: 0.55em;   /* 제목보다 작게 */
        color: #666;         /* 회색 */
        font-style: italic;  /* 기울임 */
        margin-left: .35rem; /* 약간의 간격 */
        vertical-align: super; /* 살짝 위로 올려서 뱃지 느낌 */
        ">
        beta
        </span>
    </h1>

    <p style="font-size: 1.2rem; color: #666;">생성형 AI를 활용한 교수학습 솔루션</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 👋 환영합니다! 사용자 이름을 입력하고, 유형을 선택해주세요.")
    
    # 사용자 이름 입력
    user_name = st.text_input("이름을 입력해주세요", placeholder="예: 홍길동")
    
    if not user_name:
        st.warning("이름을 입력해주세요.")
        return
    
    # 역할 선택을 위한 3개 컬럼 레이아웃
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎓 학습자", key="student", use_container_width=True, type="primary"):
            set_user_role("student")
            set_user_name(user_name)
            st.rerun()
        
        st.markdown("""
        **학습자 기능:**
        - 강의 수강신청 및 참여
        - 강의자료 다운로드 및 학습
        - AI 챗봇과 학습 상담
        - 개인 학습노트 작성
        - AI 학습도구 활용
        """)
    
    with col2:
        if st.button("👨‍🏫 교수자", key="instructor", use_container_width=True, type="primary"):
            set_user_role("instructor")
            set_user_name(user_name)
            st.rerun()
        
        st.markdown("""
        **교수자 기능:**
        - 강의 개설 및 관리
        - 강의자료 업로드 및 공유
        - AI 어시스턴트 활용 수업 준비
        - 학습자 수강 현황 분석
        - 교수학습 도구 설정
        """)
    
    with col3:
        if st.button("🛠️ 관리자", key="admin", use_container_width=True, type="primary"):
            set_user_role("admin")
            set_user_name(user_name)
            st.rerun()
        
        st.markdown("""
        **관리자 기능:**
        - 전체 시스템 현황 모니터링
        - 사용자 계정 관리
        - 통계 및 분석 리포트
        - 시스템 설정 및 유지보수
        - 플랫폼 운영 관리
        """)
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.9rem;">
        <p>🔒 이 플랫폼은 교육 목적으로 개발된 데모 버전입니다.</p>
        <p>실제 강의 운영 시에는 별도의 인증 시스템이 적용됩니다.</p>
    </div>
    """, unsafe_allow_html=True) 