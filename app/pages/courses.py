import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import sys
from pathlib import Path

# 현재 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from database.models import DatabaseManager
from utils.session_utils import get_user_name, get_user_role

def init_course_data():
    """강의 데이터 초기화"""
    if 'courses' not in st.session_state:
        st.session_state.courses = {}
    if 'course_enrollments' not in st.session_state:
        st.session_state.course_enrollments = {}
    if 'course_materials' not in st.session_state:
        st.session_state.course_materials = {}

def show_instructor_courses():
    """교수자 강의 관리 페이지"""
    init_course_data()
    
    st.markdown("### 📚 강의 관리")
    
    # 탭으로 구분
    tab1, tab2 = st.tabs(["강의 개설", "내 강의"])
    
    with tab1:
        show_create_course_form()
        
        # 새로 생성된 강의가 있으면 바로가기 버튼 표시
        if 'new_course_created' in st.session_state:
            course_info = st.session_state.new_course_created
            
            st.markdown("---")
            st.markdown("### 🎉 강의 개설 완료!")
            
            # col1, col2 = st.columns(2)
            # with col1:
            #     if st.button("🏛️ 바로 강의실 입장하기", type="primary", key="direct_enter_classroom"):
            #         st.session_state.current_course = {
            #             'id': course_info['course_id'],
            #             'data': course_info['course_data'],
            #             'entered_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #         }
            #         # 플래그 제거
            #         del st.session_state.new_course_created
            #         st.success(f"🎉 '{course_info['course_name']}' 강의실로 이동합니다!")
            #         st.rerun()
            
            # with col2:
            #     if st.button("📚 강의 목록으로 이동", type="secondary", key="goto_course_list"):
            #         # 플래그 제거하고 강의 목록 탭으로 이동
            #         del st.session_state.new_course_created
            #         st.rerun()
    
    with tab2:
        show_instructor_course_list()

def show_create_course_form():
    """강의 개설 폼"""
    st.markdown("#### 새 강의 개설")
    
    with st.form("create_course_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            course_name = st.text_input("강의명", placeholder="예: 인공지능개론")
            course_code = st.text_input("강의코드", placeholder="예: AI101")
            credit = st.selectbox("학점", [1, 2, 3, 4, 5])
        
        with col2:
            semester = st.selectbox("학기", ["2024-1", "2024-2", "2025-1", "2025-2"])
            max_students = st.number_input("수강 정원", min_value=1, max_value=200, value=30)
            department = st.text_input("개설학과", placeholder="예: 컴퓨터공학과")
        
        description = st.text_area("강의 설명", placeholder="강의 목표와 내용을 설명해주세요.")
        
        submitted = st.form_submit_button("강의 개설", type="primary")
        
        if submitted:
            if course_name and course_code:
                # 데이터베이스 매니저 초기화
                if 'db_manager' not in st.session_state:
                    st.session_state.db_manager = DatabaseManager()
                
                db_manager = st.session_state.db_manager
                user_name = get_user_name()
                
                # 교수자 정보 조회
                instructor = db_manager.get_user_by_name_role(user_name, "instructor")
                
                if not instructor:
                    # 교수자가 없으면 생성
                    instructor_id = db_manager.create_user(user_name, "instructor")
                else:
                    instructor_id = instructor['id']
                
                try:
                    # 데이터베이스에 강의 생성
                    course_id = db_manager.create_course(
                        name=course_name,
                        code=course_code,
                        instructor_id=instructor_id,
                        semester=semester,
                        credit=credit,
                        max_students=max_students,
                        department=department,
                        description=description
                    )
                    
                    # 세션 상태에도 저장 (하위 호환성을 위해)
                    if 'courses' not in st.session_state:
                        st.session_state.courses = {}
                    
                    st.session_state.courses[course_id] = {
                        'id': course_id,
                        'name': course_name,
                        'code': course_code,
                        'credit': credit,
                        'semester': semester,
                        'max_students': max_students,
                        'department': department,
                        'description': description,
                        'instructor': user_name,
                        'instructor_id': instructor_id,
                        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'is_active': True
                    }
                    
                    # 수강신청 및 강의자료 데이터 초기화
                    if 'course_enrollments' not in st.session_state:
                        st.session_state.course_enrollments = {}
                    if 'course_materials' not in st.session_state:
                        st.session_state.course_materials = {}
                    
                    st.session_state.course_enrollments[course_id] = []
                    st.session_state.course_materials[course_id] = []
                    
                    # 성공 메시지 표시
                    st.success(f"🎉 **'{course_name}' 강의가 성공적으로 개설되었습니다!**")
                    
                    # 상세 정보 표시
                    with st.expander("📋 개설된 강의 정보", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**강의명:** {course_name}")
                            st.write(f"**강의코드:** {course_code}")
                            st.write(f"**학점:** {credit}학점")
                            st.write(f"**학기:** {semester}")
                        
                        with col2:
                            st.write(f"**담당교수:** {user_name}")
                            st.write(f"**개설학과:** {department}")
                            st.write(f"**수강정원:** {max_students}명")
                            st.write(f"**개설일:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                        
                        if description:
                            st.write(f"**강의설명:** {description}")
                    
                    # 다음 단계 안내
                    st.info("💡 **다음 단계:**\n"
                           "1. 🏛️ **강의실 입장**: 강의실에서 자료를 업로드하고 관리하세요\n"
                           "2. 📚 **강의자료 업로드**: 학생들이 학습할 수 있도록 자료를 준비하세요\n"
                           "3. 👥 **수강생 관리**: 수강신청한 학생들을 확인하고 관리하세요")
                    
                    # 강의실 입장 플래그 설정
                    st.session_state.new_course_created = {
                        'course_id': course_id,
                        'course_name': course_name,
                        'course_data': st.session_state.courses[course_id]
                    }
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 강의 개설 중 오류가 발생했습니다: {str(e)}")
                    
            else:
                st.error("❌ 강의명과 강의코드는 필수 항목입니다.")

def show_instructor_course_list():
    """교수자의 강의 목록"""
    st.markdown("#### 개설한 강의 목록")
    
    # 데이터베이스 매니저 초기화
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    user_name = get_user_name()
    
    # 교수자 정보 조회
    instructor = db_manager.get_user_by_name_role(user_name, "instructor")
    
    if not instructor:
        st.info("교수자 정보를 찾을 수 없습니다. 먼저 강의를 개설해보세요!")
        return
    
    # 데이터베이스에서 강의 목록 조회
    courses_list = db_manager.get_courses_by_instructor(instructor['id'])
    
    if not courses_list:
        st.info("아직 개설한 강의가 없습니다. 새 강의를 개설해보세요!")
        return
    
    for course in courses_list:
        course_id = course['id']
        
        with st.expander(f"📖 {course['name']} ({course['code']}) - {course['semester']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**학점:** {course['credit']}학점")
                st.write(f"**학과:** {course.get('department', 'N/A')}")
                st.write(f"**개설일:** {course['created_at']}")
            
            with col2:
                # 데이터베이스에서 수강생 수와 자료 수 조회
                enrolled_students = db_manager.get_course_enrollments(course_id)
                enrolled_count = len(enrolled_students)
                st.write(f"**수강인원:** {enrolled_count}/{course['max_students']}명")
                
                documents = db_manager.get_course_documents(course_id)
                materials_count = len(documents)
                st.write(f"**업로드 자료:** {materials_count}개")
            
            with col3:
                if st.button(f"🏛️ 강의실 입장", key=f"enter_classroom_{course_id}", type="primary"):
                    st.session_state.current_course = {
                        'id': course_id,
                        'data': course,
                        'entered_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.success(f"🎉 '{course['name']}' 강의실에 입장했습니다!")
                    st.rerun()
                
                if st.button(f"강의 {'비활성화' if course.get('is_active', 1) else '활성화'}", 
                           key=f"toggle_{course_id}"):
                    # TODO: 데이터베이스에서 강의 상태 업데이트 구현 필요
                    st.info("강의 상태 변경 기능은 곧 구현될 예정입니다.")
            
            if course.get('description'):
                st.write(f"**설명:** {course['description']}")
            
            # 수강생 목록
            if enrolled_students:
                st.write("**수강생 목록:**")
                for student in enrolled_students:
                    st.write(f"- {student['name']} (수강신청일: {student['enrolled_at']})")

def show_course_materials_management():
    """강의자료 관리"""
    st.markdown("#### 강의자료 관리")
    
    # 강의 선택
    instructor_courses = {k: v for k, v in st.session_state.courses.items() 
                         if v['instructor'] == st.session_state.user_name}
    
    if not instructor_courses:
        st.info("먼저 강의를 개설해주세요.")
        return
    
    course_options = {f"{course['name']} ({course['code']})": course_id 
                     for course_id, course in instructor_courses.items()}
    
    selected_course_name = st.selectbox("강의 선택", list(course_options.keys()))
    
    if selected_course_name:
        course_id = course_options[selected_course_name]
        course = st.session_state.courses[course_id]
        
        st.markdown(f"**선택된 강의:** {course['name']}")
        
        # 파일 업로드
        st.markdown("##### 📎 강의자료 업로드")
        uploaded_files = st.file_uploader(
            "강의자료를 업로드하세요", 
            accept_multiple_files=True,
            type=['pdf', 'ppt', 'pptx', 'doc', 'docx', 'txt', 'jpg', 'png', 'mp4', 'mp3']
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if st.button(f"'{uploaded_file.name}' 업로드", key=f"upload_{uploaded_file.name}"):
                    # 파일 정보 저장
                    file_info = {
                        'id': str(uuid.uuid4())[:8],
                        'name': uploaded_file.name,
                        'size': uploaded_file.size,
                        'type': uploaded_file.type,
                        'uploaded_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'uploader': st.session_state.user_name
                    }
                    
                    if course_id not in st.session_state.course_materials:
                        st.session_state.course_materials[course_id] = []
                    
                    st.session_state.course_materials[course_id].append(file_info)
                    st.success(f"✅ '{uploaded_file.name}' 파일이 업로드되었습니다!")
                    st.rerun()
        
        # 업로드된 자료 목록
        st.markdown("##### 📚 업로드된 강의자료")
        materials = st.session_state.course_materials.get(course_id, [])
        
        if materials:
            for material in materials:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"📄 **{material['name']}**")
                        st.caption(f"업로드: {material['uploaded_at']}")
                    
                    with col2:
                        file_size_kb = material['size'] / 1024
                        st.write(f"크기: {file_size_kb:.1f} KB")
                    
                    with col3:
                        if st.button("삭제", key=f"delete_{material['id']}"):
                            st.session_state.course_materials[course_id] = [
                                m for m in materials if m['id'] != material['id']
                            ]
                            st.rerun()
        else:
            st.info("아직 업로드된 강의자료가 없습니다.")

def show_student_courses():
    """학생 강의 목록 및 참여"""
    init_course_data()
    
    st.markdown("### 📚 강의 참여")
    
    tab1, tab2 = st.tabs(["수강신청", "내 강의"])
    
    with tab1:
        show_course_enrollment()
    
    with tab2:
        show_enrolled_courses()

def show_course_enrollment():
    """수강신청 페이지"""
    st.markdown("#### 수강신청")
    
    # 활성화된 강의만 표시
    active_courses = {k: v for k, v in st.session_state.courses.items() if v['is_active']}
    
    if not active_courses:
        st.info("현재 수강신청 가능한 강의가 없습니다.")
        return
    
    for course_id, course in active_courses.items():
        enrolled_count = len(st.session_state.course_enrollments.get(course_id, []))
        is_enrolled = any(student['name'] == st.session_state.user_name 
                         for student in st.session_state.course_enrollments.get(course_id, []))
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**📖 {course['name']} ({course['code']})**")
                st.write(f"교수자: {course['instructor']} | 학점: {course['credit']} | 학기: {course['semester']}")
                st.write(f"수강인원: {enrolled_count}/{course['max_students']}명")
                st.write(f"설명: {course['description']}")
            
            with col2:
                if is_enrolled:
                    st.success("✅ 수강중")
                elif enrolled_count >= course['max_students']:
                    st.error("❌ 정원초과")
                else:
                    if st.button("수강신청", key=f"enroll_{course_id}"):
                        # 수강신청 처리
                        enrollment_info = {
                            'name': st.session_state.user_name,
                            'enrollment_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        if course_id not in st.session_state.course_enrollments:
                            st.session_state.course_enrollments[course_id] = []
                        
                        st.session_state.course_enrollments[course_id].append(enrollment_info)
                        st.success(f"✅ '{course['name']}' 강의에 수강신청되었습니다!")
                        st.rerun()
            
            st.divider()

def show_enrolled_courses():
    """수강중인 강의 목록"""
    st.markdown("#### 수강중인 강의")
    
    # 내가 수강중인 강의 찾기
    my_courses = []
    for course_id, enrollments in st.session_state.course_enrollments.items():
        if any(student['name'] == st.session_state.user_name for student in enrollments):
            course_info = st.session_state.courses[course_id]
            my_courses.append((course_id, course_info))
    
    if not my_courses:
        st.info("수강중인 강의가 없습니다. 수강신청을 해보세요!")
        return
    
    for course_id, course in my_courses:
        with st.expander(f"📖 {course['name']} ({course['code']})"):
            st.write(f"**교수자:** {course['instructor']}")
            st.write(f"**학점:** {course['credit']}학점")
            st.write(f"**학기:** {course['semester']}")
            st.write(f"**설명:** {course['description']}")
            
            # 강의자료 표시
            st.markdown("##### 📚 강의자료")
            materials = st.session_state.course_materials.get(course_id, [])
            
            if materials:
                for material in materials:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"📄 {material['name']}")
                        st.caption(f"업로드: {material['uploaded_at']}")
                    
                    with col2:
                        file_size_kb = material['size'] / 1024
                        st.caption(f"{file_size_kb:.1f} KB")
                        st.button("다운로드", key=f"download_{material['id']}", 
                                disabled=True, help="다운로드 기능은 추후 구현 예정")
            else:
                st.info("아직 업로드된 강의자료가 없습니다.") 