import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# 현재 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from utils.session_utils import get_user_name, get_user_role
from services.document_service import DocumentService
from database.models import DatabaseManager

def show_student_home():
    """학습자 홈 페이지"""
    user_name = get_user_name()
    
    st.markdown(f"### 🎯 {user_name}님의 학습 현황")
    
    # 실제 데이터 계산
    enrolled_courses = get_student_enrolled_courses(user_name)
    total_materials = get_student_accessible_materials(user_name)
    
    # 메트릭 표시
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📚 수강 중인 강의", f"{len(enrolled_courses)}개")
    with col2:
        st.metric("📁 이용 가능한 자료", f"{total_materials}개")
    with col3:
        st.metric("📝 학습노트", "0개", help="곧 구현될 예정입니다")
    with col4:
        st.metric("🎨 AI 도구 사용", "0회", help="곧 구현될 예정입니다")
    
    st.markdown("---")
    
    # 수강 중인 강의 목록
    if enrolled_courses:
        st.markdown("### 📚 수강 중인 강의")
        
        # 데이터베이스 매니저 초기화
        if 'db_manager' not in st.session_state:
            st.session_state.db_manager = DatabaseManager()
        
        db_manager = st.session_state.db_manager
        
        # 사용자 정보 조회
        user = db_manager.get_user_by_name_role(user_name, "student")
        if not user:
            st.error("사용자 정보를 찾을 수 없습니다.")
            return
        
        # 학생의 수강 강의 목록 조회 (상세 정보 포함)
        student_courses = db_manager.get_student_courses(user['id'])
        
        courses_data = []
        for course in student_courses:
            # 각 강의의 자료 수 조회
            materials_count = len(db_manager.get_course_documents(course['id']))
            
            courses_data.append({
                '강의명': course['name'],
                '강의코드': course['code'],
                '담당교수': course['instructor_name'],
                '학기': course['semester'],
                '강의자료': f"{materials_count}개"
            })
        
        if courses_data:
            df_courses = pd.DataFrame(courses_data)
            st.dataframe(df_courses, use_container_width=True)
            
            # 강의실 바로가기
            st.markdown("#### 🏛️ 강의실 바로가기")
            cols = st.columns(min(len(courses_data), 3))
            for i, course in enumerate(student_courses):
                with cols[i % 3]:
                    if st.button(f"📖 {course['name']}", key=f"goto_course_{i}"):
                        # 강의실 입장 로직
                        st.session_state.current_course = {
                            'id': course['id'],
                            'data': course,
                            'entered_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.success(f"🎉 '{course['name']}' 강의실로 이동합니다!")
                        st.rerun()
    else:
        st.info("👋 아직 수강 중인 강의가 없습니다. '📚 내 강의'에서 강의를 신청해보세요!")
    
    # 추천 기능 (향후 구현)
    st.markdown("---")
    st.markdown("### 💡 추천 기능")
    st.info("🚀 AI 기반 학습 추천 기능이 곧 추가될 예정입니다!")

def show_instructor_home():
    """교수자 홈 페이지"""
    user_name = get_user_name()
    
    st.markdown(f"### 📊 {user_name} 교수님의 수업 현황")
    
    # 실제 데이터 계산
    instructor_courses = get_instructor_courses(user_name)
    total_students = get_instructor_total_students(user_name)
    total_materials = get_instructor_total_materials(user_name)
    
    # 메트릭 표시
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📚 개설 강의", f"{len(instructor_courses)}개")
    with col2:
        st.metric("👥 총 수강생", f"{total_students}명")
    with col3:
        st.metric("📁 업로드한 자료", f"{total_materials}개")
    with col4:
        st.metric("🤖 AI 활용률", "0%", help="곧 구현될 예정입니다")
    
    st.markdown("---")
    
    # 담당 수업 정보
    if instructor_courses:
        st.markdown("### 📚 담당 수업")
        
        # 데이터베이스 매니저 초기화
        if 'db_manager' not in st.session_state:
            st.session_state.db_manager = DatabaseManager()
        
        db_manager = st.session_state.db_manager
        
        courses_data = []
        for course_id, course in instructor_courses.items():
            # 데이터베이스에서 수강생 수와 자료 수 조회
            enrolled_count = len(db_manager.get_course_enrollments(course_id))
            materials_count = len(db_manager.get_course_documents(course_id))
            
            courses_data.append({
                '수업명': course['name'],
                '강의코드': course['code'],
                '학기': course['semester'],
                '수강생': f"{enrolled_count}/{course['max_students']}명",
                '자료': f"{materials_count}개",
                '상태': "활성" if course.get('is_active', 1) else "비활성"
            })
        
        if courses_data:
            df_courses = pd.DataFrame(courses_data)
            
            # 클릭 가능한 데이터 테이블
            st.markdown("#### 📊 강의 목록")
            selected_rows = st.data_editor(
                df_courses,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "수업명": st.column_config.TextColumn("🏛️ 수업명", width="medium"),
                    "강의코드": st.column_config.TextColumn("📋 강의코드", width="small"),
                    "학기": st.column_config.TextColumn("📅 학기", width="small"),
                    "수강생": st.column_config.TextColumn("👥 수강생", width="small"),
                    "자료": st.column_config.TextColumn("📁 자료", width="small"),
                    "상태": st.column_config.TextColumn("🔄 상태", width="small"),
                },
                disabled=True,  # 편집 불가능하게 설정
                key="courses_table"
            )
            
            # # 강의 선택 드롭다운
            # st.markdown("#### 🎯 강의실 입장")
            # course_options = [f"{course['수업명']} ({course['강의코드']})" for course in courses_data]
            # selected_course_idx = st.selectbox(
            #     "입장할 강의를 선택하세요:",
            #     options=range(len(course_options)),
            #     format_func=lambda x: course_options[x],
            #     key="course_selector"
            # )
            
            # # 입장 버튼
            # col1, col2 = st.columns([1, 4])
            # with col1:
            #     if st.button("🚀 강의실 입장", type="primary", use_container_width=True):
            #         # 선택된 강의 정보 가져오기
            #         course_list = list(instructor_courses.items())
            #         selected_course_id, selected_course_data = course_list[selected_course_idx]
                    
            #         # 강의실 입장 로직
            #         st.session_state.current_course = {
            #             'id': selected_course_id,
            #             'data': selected_course_data,
            #             'entered_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #         }
            #         st.success(f"🎉 '{selected_course_data['name']}' 강의실로 이동합니다!")
            #         st.rerun()
            
            # with col2:
            #     if st.button("📊 강의 상세 정보", use_container_width=True):
            #         # 선택된 강의의 상세 정보 표시
            #         course_list = list(instructor_courses.items())
            #         selected_course_id, selected_course_data = course_list[selected_course_idx]
                    
            #         with st.expander(f"📋 {selected_course_data['name']} 상세 정보", expanded=True):
            #             col_info1, col_info2 = st.columns(2)
            #             with col_info1:
            #                 st.write(f"**강의명:** {selected_course_data['name']}")
            #                 st.write(f"**강의코드:** {selected_course_data['code']}")
            #                 st.write(f"**학기:** {selected_course_data['semester']}")
            #             with col_info2:
            #                 enrolled_count = len(db_manager.get_course_enrollments(selected_course_id))
            #                 materials_count = len(db_manager.get_course_documents(selected_course_id))
            #                 st.write(f"**수강생:** {enrolled_count}/{selected_course_data['max_students']}명")
            #                 st.write(f"**강의자료:** {materials_count}개")
            #                 st.write(f"**상태:** {'활성' if selected_course_data.get('is_active', 1) else '비활성'}")
            
            # 최근 활동 (수강생 등록, 자료 업로드 등)
            st.markdown("---")
            st.markdown("### 📋 최근 활동")
            recent_activities = get_instructor_recent_activities(user_name)
            
            if recent_activities:
                df_activities = pd.DataFrame(recent_activities)
                st.dataframe(df_activities, use_container_width=True)
            else:
                st.info("최근 활동이 없습니다.")
    else:
        st.info("👋 아직 개설한 강의가 없습니다. '📚 강의 관리'에서 새 강의를 개설해보세요!")
    


def show_admin_home():
    """관리자 홈 페이지"""
    st.markdown("### 🖥️ 시스템 현황")
    
    # 메트릭 표시
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 전체 사용자", "289명", "↗️ 12")
    with col2:
        st.metric("🖥️ 서버 상태", "정상", "✅")
    with col3:
        st.metric("💾 저장소 사용률", "45%", "↗️ 3%")
    with col4:
        st.metric("🔥 일일 접속", "156명", "↗️ 23")
    
    st.markdown("---")
    
    # 시스템 알림
    st.markdown("### 🔔 시스템 알림")
    notifications = [
        {"시간": "2024-01-15 15:00", "유형": "⚠️ 경고", "내용": "저장소 사용률이 45%를 초과했습니다."},
        {"시간": "2024-01-15 14:30", "유형": "ℹ️ 정보", "내용": "시스템 백업이 완료되었습니다."},
        {"시간": "2024-01-15 13:45", "유형": "✅ 성공", "내용": "새로운 사용자 12명이 등록되었습니다."}
    ]
    
    df_notifications = pd.DataFrame(notifications)
    st.dataframe(df_notifications, use_container_width=True)

# 헬퍼 함수들
def get_student_enrolled_courses(user_name: str) -> list:
    """학생이 수강 중인 강의 ID 목록 반환"""
    # 데이터베이스 매니저 초기화
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    
    # 사용자 ID 조회
    user = db_manager.get_user_by_name_role(user_name, "student")
    if not user:
        return []
    
    # 학생의 수강 강의 목록 조회
    courses = db_manager.get_student_courses(user['id'])
    
    # 강의 ID 목록 반환
    return [course['id'] for course in courses]

def get_student_accessible_materials(user_name: str) -> int:
    """학생이 접근 가능한 강의자료 수"""
    # 데이터베이스 매니저 초기화
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    enrolled_courses = get_student_enrolled_courses(user_name)
    total_materials = 0
    
    # 각 수강 강의의 문서 수 계산
    for course_id in enrolled_courses:
        documents = db_manager.get_course_documents(course_id)
        total_materials += len(documents)
    
    return total_materials

def get_instructor_courses(user_name: str) -> dict:
    """교수자가 개설한 강의 목록 반환"""
    # 데이터베이스 매니저 초기화
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    
    # 사용자 ID 조회
    user = db_manager.get_user_by_name_role(user_name, "instructor")
    if not user:
        return {}
    
    # 교수자의 강의 목록 조회
    courses_list = db_manager.get_courses_by_instructor(user['id'])
    
    # 딕셔너리 형태로 변환
    instructor_courses = {}
    for course in courses_list:
        instructor_courses[course['id']] = course
    
    return instructor_courses

def get_instructor_total_students(user_name: str) -> int:
    """교수자의 총 수강생 수"""
    # 데이터베이스 매니저 초기화
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    instructor_courses = get_instructor_courses(user_name)
    total_students = 0
    
    # 각 강의의 수강생 수 계산
    for course_id in instructor_courses.keys():
        enrollments = db_manager.get_course_enrollments(course_id)
        total_students += len(enrollments)
    
    return total_students

def get_instructor_total_materials(user_name: str) -> int:
    """교수자가 업로드한 총 자료 수"""
    # 데이터베이스 매니저 초기화
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    instructor_courses = get_instructor_courses(user_name)
    total_materials = 0
    
    # 각 강의의 문서 수 계산
    for course_id in instructor_courses.keys():
        documents = db_manager.get_course_documents(course_id)
        total_materials += len(documents)
    
    return total_materials

def get_instructor_recent_activities(user_name: str) -> list:
    """교수자의 최근 활동 목록"""
    # 데이터베이스 매니저 초기화
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    activities = []
    instructor_courses = get_instructor_courses(user_name)
    
    # 강의 개설 활동
    for course_id, course in instructor_courses.items():
        activities.append({
            '시간': course.get('created_at', '알 수 없음'),
            '활동': '📚 강의 개설',
            '내용': f"'{course['name']}' 강의 개설"
        })
    
    # 자료 업로드 활동 (각 강의별로 최근 문서들)
    for course_id in instructor_courses.keys():
        documents = db_manager.get_course_documents(course_id)
        for doc in documents[:5]:  # 각 강의당 최근 5개만
            activities.append({
                '시간': doc.get('uploaded_at', '알 수 없음'),
                '활동': '📤 자료 업로드',
                '내용': f"'{doc['original_filename']}' 파일 업로드"
            })
    
    # 시간순 정렬 (최신순)
    activities.sort(key=lambda x: x['시간'], reverse=True)
    
    return activities[:10]  # 최근 10개만 반환 