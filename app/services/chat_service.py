import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
import json

from database.models import DatabaseManager
from ai.search_engine import AISearchEngine
from vector.faiss_manager import FAISSVectorManager

logger = logging.getLogger(__name__)

class ChatService:
    """AI 채팅 서비스"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """초기화"""
        self.db_manager = db_manager or DatabaseManager()
        self.search_engine = AISearchEngine(self.db_manager)
        
        # OpenAI API 설정 (실제 환경에서는 환경변수로 설정)
        self.openai_api_key = None  # 실제 키 필요
        self.openai_base_url = "https://api.openai.com/v1"
        
        logger.info("채팅 서비스 초기화 완료")
    
    def create_chat_room(self, user_id: str, course_id: str, title: str = None) -> Dict:
        """
        채팅방 생성
        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            title: 채팅방 제목 (None이면 자동 생성)
        Returns:
            채팅방 생성 결과
        """
        try:
            # 임시 제목 설정
            if not title:
                title = f"채팅방 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # 채팅방 생성
            room_id = self.db_manager.create_chat_room(user_id, course_id, title)
            
            return {
                'success': True,
                'room_id': room_id,
                'title': title,
                'message': '채팅방이 생성되었습니다.'
            }
            
        except Exception as e:
            logger.error(f"채팅방 생성 중 오류: {str(e)}")
            return {
                'success': False,
                'message': f'채팅방 생성 중 오류가 발생했습니다: {str(e)}'
            }
    
    def get_user_chat_rooms(self, user_id: str, course_id: str = None) -> List[Dict]:
        """사용자 채팅방 목록 조회"""
        try:
            rooms = self.db_manager.get_user_chat_rooms(user_id, course_id)
            
            # 각 채팅방의 마지막 메시지 정보 추가
            for room in rooms:
                messages = self.db_manager.get_chat_messages(room['id'], limit=1)
                if messages:
                    room['last_message'] = messages[-1]['content'][:100] + '...' if len(messages[-1]['content']) > 100 else messages[-1]['content']
                    room['last_message_time'] = messages[-1]['created_at']
                else:
                    room['last_message'] = None
                    room['last_message_time'] = None
            
            return rooms
            
        except Exception as e:
            logger.error(f"채팅방 목록 조회 중 오류: {str(e)}")
            return []
    
    def get_chat_room(self, room_id: str) -> Optional[Dict]:
        """채팅방 조회"""
        try:
            return self.db_manager.get_chat_room(room_id)
        except Exception as e:
            logger.error(f"채팅방 조회 중 오류: {str(e)}")
            return None
    
    def get_chat_messages(self, room_id: str, limit: int = 50) -> List[Dict]:
        """채팅 메시지 조회"""
        try:
            return self.db_manager.get_chat_messages(room_id, limit)
        except Exception as e:
            logger.error(f"채팅 메시지 조회 중 오류: {str(e)}")
            return []
    
    def generate_chat_title(self, first_message: str) -> str:
        """
        첫 번째 메시지로부터 채팅방 제목 자동 생성
        Args:
            first_message: 첫 번째 메시지
        Returns:
            생성된 제목
        """
        try:
            # 간단한 제목 생성 규칙
            # 실제 구현에서는 LLM을 사용하여 더 정교한 제목 생성 가능
            
            # 특수문자 제거 및 공백 정리
            clean_message = re.sub(r'[^\w\s가-힣]', '', first_message)
            clean_message = re.sub(r'\s+', ' ', clean_message).strip()
            
            # 길이 제한
            if len(clean_message) > 30:
                clean_message = clean_message[:30] + '...'
            
            # 질문 형태 감지
            if '?' in first_message or '질문' in first_message:
                title = f"질문: {clean_message}"
            elif '설명' in first_message or '알려주세요' in first_message:
                title = f"설명: {clean_message}"
            elif '문제' in first_message or '과제' in first_message:
                title = f"문제: {clean_message}"
            else:
                title = clean_message
            
            return title if title else "새로운 채팅"
            
        except Exception as e:
            logger.error(f"제목 생성 중 오류: {str(e)}")
            return "새로운 채팅"
    
    def process_message(self, room_id: str, user_message: str) -> Dict:
        """
        메시지 처리 및 AI 응답 생성
        Args:
            room_id: 채팅방 ID
            user_message: 사용자 메시지
        Returns:
            처리 결과
        """
        try:
            # 채팅방 정보 조회
            room = self.db_manager.get_chat_room(room_id)
            if not room:
                return {
                    'success': False,
                    'message': '채팅방을 찾을 수 없습니다.'
                }
            
            # 사용자 메시지 저장
            self.db_manager.create_chat_message(room_id, 'user', user_message)
            
            # 채팅 기록 조회 (컨텍스트용)
            chat_context = self.db_manager.get_chat_context(room_id, limit=10)
            
            # 첫 번째 메시지인 경우 제목 자동 생성
            if len(chat_context) == 1:  # 방금 추가한 메시지만 있는 경우
                title = self.generate_chat_title(user_message)
                self.db_manager.update_chat_room(room_id, title=title)
                room['title'] = title
            
            # 강의자료 기반 AI 응답 생성
            ai_response = self.generate_ai_response(room['course_id'], user_message, chat_context)
            
            # AI 응답 저장
            self.db_manager.create_chat_message(room_id, 'assistant', ai_response)
            
            return {
                'success': True,
                'user_message': user_message,
                'ai_response': ai_response,
                'room_title': room['title']
            }
            
        except Exception as e:
            logger.error(f"메시지 처리 중 오류: {str(e)}")
            return {
                'success': False,
                'message': f'메시지 처리 중 오류가 발생했습니다: {str(e)}'
            }
    
    def generate_ai_response(self, course_id: str, user_message: str, chat_context: List[Dict]) -> str:
        """
        강의자료 기반 AI 응답 생성
        Args:
            course_id: 강의 ID
            user_message: 사용자 메시지
            chat_context: 채팅 컨텍스트
        Returns:
            AI 응답
        """
        try:
            # 강의자료에서 관련 문서 검색
            search_result = self.search_engine.search_documents(
                course_id=course_id,
                query=user_message,
                search_type='vector',
                top_k=3,
                min_similarity=0.3
            )
            
            # 검색 결과에서 관련 내용 추출
            relevant_content = []
            if search_result['success'] and search_result['results']:
                for result in search_result['results']:
                    relevant_content.append(result['content'])
            
            # 채팅 컨텍스트 구성
            context_messages = []
            for msg in chat_context[-5:]:  # 최근 5개 메시지만 사용
                context_messages.append(f"{msg['role']}: {msg['content']}")
            
            # AI 응답 생성
            if relevant_content:
                # 강의자료가 있는 경우
                response = self._generate_knowledge_based_response(
                    user_message, relevant_content, context_messages
                )
            else:
                # 강의자료가 없는 경우
                response = self._generate_general_response(user_message, context_messages)
            
            return response
            
        except Exception as e:
            logger.error(f"AI 응답 생성 중 오류: {str(e)}")
            return "죄송합니다. 답변을 생성하는 중 오류가 발생했습니다. 다시 시도해 주세요."
    
    def _generate_knowledge_based_response(self, user_message: str, relevant_content: List[str], context_messages: List[str]) -> str:
        """강의자료 기반 응답 생성"""
        # 실제 구현에서는 OpenAI API나 다른 LLM을 사용
        # 현재는 간단한 규칙 기반 응답
        
        content_summary = " ".join(relevant_content)[:1000]  # 길이 제한
        
        # 키워드 기반 응답 생성
        if "설명" in user_message or "무엇" in user_message:
            response = f"""강의자료를 바탕으로 설명드리겠습니다.

📚 **관련 내용:**
{content_summary}

이 내용이 도움이 되시나요? 더 자세한 설명이 필요하시면 구체적으로 질문해 주세요."""
        
        elif "예시" in user_message or "예제" in user_message:
            response = f"""강의자료에서 관련 예시를 찾아드렸습니다.

💡 **예시:**
{content_summary}

다른 예시가 필요하시면 말씀해 주세요."""
        
        else:
            response = f"""강의자료를 참고하여 답변드리겠습니다.

📖 **답변:**
{content_summary}

추가 질문이 있으시면 언제든지 말씀해 주세요."""
        
        return response
    
    def _generate_general_response(self, user_message: str, context_messages: List[str]) -> str:
        """일반적인 응답 생성"""
        # 강의자료가 없는 경우의 응답
        
        if "안녕" in user_message or "hello" in user_message.lower():
            return "안녕하세요! 저는 이 강의의 학습을 도와드리는 AI 어시스턴트입니다. 강의자료에 대한 질문이나 학습 관련 문의사항이 있으시면 언제든지 말씀해 주세요."
        
        elif "감사" in user_message or "고마워" in user_message:
            return "천만에요! 더 도움이 필요하시면 언제든지 질문해 주세요. 함께 학습해 나가요!"
        
        elif "?" in user_message:
            return "흥미로운 질문이네요! 안타깝게도 현재 이 질문에 대한 강의자료를 찾을 수 없습니다. 강의자료가 업로드되면 더 정확한 답변을 드릴 수 있을 것 같습니다. 다른 질문이 있으시면 말씀해 주세요."
        
        else:
            return "말씀하신 내용을 잘 이해했습니다. 강의자료를 바탕으로 더 구체적인 답변을 드리고 싶지만, 현재 관련 자료를 찾을 수 없습니다. 구체적인 질문이나 키워드를 사용해서 다시 질문해 주시면 더 도움이 될 것 같습니다."
    
    def delete_chat_room(self, room_id: str, user_id: str) -> Dict:
        """
        채팅방 삭제
        Args:
            room_id: 채팅방 ID
            user_id: 사용자 ID (권한 확인용)
        Returns:
            삭제 결과
        """
        try:
            # 채팅방 소유자 확인
            room = self.db_manager.get_chat_room(room_id)
            if not room:
                return {
                    'success': False,
                    'message': '채팅방을 찾을 수 없습니다.'
                }
            
            if room['user_id'] != user_id:
                return {
                    'success': False,
                    'message': '채팅방을 삭제할 권한이 없습니다.'
                }
            
            # 채팅방 삭제
            success = self.db_manager.delete_chat_room(room_id)
            
            if success:
                return {
                    'success': True,
                    'message': '채팅방이 삭제되었습니다.'
                }
            else:
                return {
                    'success': False,
                    'message': '채팅방 삭제 중 오류가 발생했습니다.'
                }
                
        except Exception as e:
            logger.error(f"채팅방 삭제 중 오류: {str(e)}")
            return {
                'success': False,
                'message': f'채팅방 삭제 중 오류가 발생했습니다: {str(e)}'
            }
    
    def get_chat_statistics(self, user_id: str) -> Dict:
        """채팅 통계 조회"""
        try:
            rooms = self.db_manager.get_user_chat_rooms(user_id)
            
            total_rooms = len(rooms)
            total_messages = 0
            
            for room in rooms:
                messages = self.db_manager.get_chat_messages(room['id'])
                total_messages += len(messages)
            
            return {
                'total_rooms': total_rooms,
                'total_messages': total_messages,
                'average_messages_per_room': total_messages / total_rooms if total_rooms > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"채팅 통계 조회 중 오류: {str(e)}")
            return {
                'total_rooms': 0,
                'total_messages': 0,
                'average_messages_per_room': 0
            } 