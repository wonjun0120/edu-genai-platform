import streamlit as st
from datetime import datetime
import uuid

from services.chat_service import ChatService
from utils.session_utils import get_user_id, get_selected_course_id

def show_chat_page():
    """AI 채팅 페이지 (강의실 내부에 표시)"""
    
    # 필수 정보 확인
    user_id = get_user_id()
    course_id = get_selected_course_id()
    if not user_id or not course_id:
        st.error("사용자 또는 강의 정보를 찾을 수 없습니다. 다시 시도해 주세요.")
        return
        
    chat_service = ChatService()
    
    # 강의별 채팅방 ID를 세션에서 관리
    room_key = f"current_chat_room_{course_id}"
    if room_key not in st.session_state:
        st.session_state[room_key] = None

    # 채팅방 목록과 채팅 영역을 두 개의 컬럼으로 분리
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### 📝 채팅방")
        
        # 새 채팅방 생성 버튼
        if st.button("🆕 새 채팅 시작하기", use_container_width=True):
            result = chat_service.create_chat_room(user_id=user_id, course_id=course_id)
            if result['success']:
                st.session_state[room_key] = result['room_id']
                st.rerun()
            else:
                st.error(result['message'])

        st.markdown("---")
        
        # 채팅방 목록 표시
        chat_rooms = chat_service.get_user_chat_rooms(user_id=user_id, course_id=course_id)
        if not chat_rooms:
            st.info("채팅 기록이 없습니다. '새 채팅 시작하기'를 눌러 대화를 시작하세요.")
        else:
            for room in chat_rooms:
                is_current = st.session_state.get(room_key) == room['id']
                button_type = "primary" if is_current else "secondary"
                if st.button(room['title'], key=f"room_{room['id']}", use_container_width=True, type=button_type):
                    st.session_state[room_key] = room['id']
                    st.rerun()
    
    with col2:
        current_room_id = st.session_state.get(room_key)
        
        if current_room_id is None:
            st.markdown("#### AI 학습 도우미")
            st.info("왼쪽에서 채팅방을 선택하거나 새 채팅을 시작해주세요.")
            # 여기에 AI 도우미 사용법 안내 등을 추가할 수 있습니다.
            return
            
        # --- 실제 채팅이 이루어지는 영역 ---
        current_room = chat_service.get_chat_room(current_room_id)
        if not current_room:
            st.error("채팅방 정보를 불러올 수 없습니다.")
            st.session_state[room_key] = None
            return

        st.markdown(f"#### {current_room['title']}")
        
        # 메시지 표시 영역
        message_container = st.container()
        with message_container:
            messages = chat_service.get_chat_messages(current_room_id)
            for message in messages:
                with st.chat_message(message['role']):
                    st.markdown(message['content'])

        # 메시지 입력
        if prompt := st.chat_input("강의 내용에 대해 질문해보세요..."):
            with st.spinner("AI가 답변을 생성하고 있습니다..."):
                chat_service.process_message(room_id=current_room_id, user_message=prompt)
                st.rerun() 