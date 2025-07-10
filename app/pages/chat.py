import streamlit as st

def show_chat_page():
    """AI 챗봇 페이지"""
    st.markdown("### 💬 AI 챗봇")
    
    # 채팅 히스토리 표시
    chat_history = st.session_state.get('chat_history', [])
    
    if chat_history:
        st.markdown("#### 💬 대화 기록")
        for message in chat_history:
            if message["role"] == "user":
                st.markdown(f"**👤 사용자:** {message['content']}")
            else:
                st.markdown(f"**🤖 AI:** {message['content']}")
        st.markdown("---")
    
    # 메시지 입력 폼
    with st.form(key="chat_form"):
        user_input = st.text_area("질문을 입력하세요:", height=100, key="chat_input")
        col1, col2 = st.columns([1, 4])
        
        with col1:
            submit_button = st.form_submit_button("전송", use_container_width=True)
        
        with col2:
            if st.form_submit_button("대화 기록 지우기", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
    
    # 메시지 처리
    if submit_button and user_input:
        # 사용자 메시지 추가
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # AI 응답 (현재는 더미 응답)
        ai_response = f"'{user_input}'에 대한 답변입니다. (현재 더미 응답 - 실제 AI 연동 예정)"
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        
        st.rerun()
    
    # 도움말
    with st.expander("💡 사용 팁"):
        st.markdown("""
        - 구체적인 질문을 하시면 더 정확한 답변을 받을 수 있습니다.
        - 파일을 업로드하신 경우, 해당 내용을 바탕으로 답변드립니다.
        - Phase 2에서 실제 AI 연동이 완료될 예정입니다.
        """) 