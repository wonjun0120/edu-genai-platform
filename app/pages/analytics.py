import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 현재 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from database.models import DatabaseManager
from utils.session_utils import get_user_name, get_user_role

def show_analytics_page():
    """분석 페이지"""
    user_name = get_user_name()
    user_role = get_user_role()
    
    if user_role == "instructor":
        show_instructor_analytics()
    elif user_role == "admin":
        show_admin_analytics()
    else:
        st.info("👋 분석 기능은 교수자와 관리자만 이용할 수 있습니다.")

def show_instructor_analytics():
    """교수자 분석 페이지"""
    user_name = get_user_name()
    
    st.markdown(f"### 📊 {user_name} 교수님의 수업 분석")
    
    # 데이터베이스 매니저 초기화
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    
    # 교수자 정보 조회
    instructor = db_manager.get_user_by_name_role(user_name, "instructor")
    
    if not instructor:
        st.error("교수자 정보를 찾을 수 없습니다.")
        return
    
    # 교수자의 강의 목록 조회
    courses = db_manager.get_courses_by_instructor(instructor['id'])
    
    if not courses:
        st.info("📚 분석할 강의가 없습니다. 먼저 강의를 개설해보세요!")
        return
    
    # 탭으로 구분
    tabs = st.tabs(["📈 강의 현황", "👥 수강생 분석", "📚 자료 분석", "🔍 상세 리포트"])
    
    with tabs[0]:
        show_course_overview_analytics(db_manager, courses)
    
    with tabs[1]:
        show_student_analytics(db_manager, courses)
    
    with tabs[2]:
        show_material_analytics(db_manager, courses)
    
    with tabs[3]:
        show_instructor_detailed_reports(db_manager, courses)

def show_admin_analytics():
    """관리자 분석 페이지"""
    st.markdown("### 📊 관리자 분석 대시보드")
    
    # 탭으로 구분
    tabs = st.tabs(["📈 시스템 현황", "👥 사용자 분석", "📚 학습 분석", "🔍 상세 리포트"])
    
    with tabs[0]:
        show_system_analytics()
    
    with tabs[1]:
        show_user_analytics()
    
    with tabs[2]:
        show_learning_analytics()
    
    with tabs[3]:
        show_detailed_reports()

def show_course_overview_analytics(db_manager, courses):
    """강의 현황 분석"""
    st.markdown("#### 📈 강의 현황 분석")
    
    # 전체 통계 계산
    total_courses = len(courses)
    total_students = 0
    total_documents = 0
    
    course_stats = []
    
    for course in courses:
        course_id = course['id']
        enrollments = db_manager.get_course_enrollments(course_id)
        documents = db_manager.get_course_documents(course_id)
        
        total_students += len(enrollments)
        total_documents += len(documents)
        
        course_stats.append({
            '강의명': course['name'],
            '학기': course['semester'],
            '수강생': len(enrollments),
            '정원': course['max_students'],
            '자료 수': len(documents),
            '개설일': course['created_at']
        })
    
    # 메트릭 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 강의 수", f"{total_courses}개")
    
    with col2:
        st.metric("총 수강생", f"{total_students}명")
    
    with col3:
        st.metric("총 자료 수", f"{total_documents}개")
    
    with col4:
        avg_students_per_course = total_students / total_courses if total_courses > 0 else 0
        st.metric("강의당 평균 수강생", f"{avg_students_per_course:.1f}명")
    
    # 강의별 상세 현황
    st.markdown("#### 📚 강의별 상세 현황")
    
    if course_stats:
        df_stats = pd.DataFrame(course_stats)
        st.dataframe(df_stats, use_container_width=True)
        
        # 수강생 수 차트
        st.markdown("#### 📊 강의별 수강생 현황")
        chart_data = df_stats.set_index('강의명')['수강생']
        st.bar_chart(chart_data)
    else:
        st.info("분석할 강의 데이터가 없습니다.")

def show_student_analytics(db_manager, courses):
    """수강생 분석"""
    st.markdown("#### 👥 수강생 분석")
    
    student_data = []
    all_enrollments = []
    
    for course in courses:
        course_id = course['id']
        enrollments = db_manager.get_course_enrollments(course_id)
        
        for enrollment in enrollments:
            student_data.append({
                '강의명': course['name'],
                '학생명': enrollment['name'],
                '수강신청일': enrollment['enrolled_at'],
                '상태': enrollment['status']
            })
            all_enrollments.append(enrollment)
    
    if not student_data:
        st.info("수강생 데이터가 없습니다.")
        return
    
    # 수강생 현황 메트릭
    col1, col2, col3 = st.columns(3)
    
    with col1:
        unique_students = len(set(s['학생명'] for s in student_data))
        st.metric("총 수강생", f"{unique_students}명")
    
    with col2:
        active_students = len([s for s in student_data if s['상태'] == 'active'])
        st.metric("활성 수강생", f"{active_students}명")
    
    with col3:
        avg_courses_per_student = len(student_data) / unique_students if unique_students > 0 else 0
        st.metric("학생당 평균 수강 강의", f"{avg_courses_per_student:.1f}개")
    
    # 수강생 목록
    st.markdown("#### 📋 수강생 목록")
    df_students = pd.DataFrame(student_data)
    st.dataframe(df_students, use_container_width=True)
    
    # 수강신청 추이 (월별)
    st.markdown("#### 📈 수강신청 추이")
    
    # 수강신청 날짜별 그룹화
    df_students['월'] = pd.to_datetime(df_students['수강신청일']).dt.to_period('M')
    monthly_enrollments = df_students.groupby('월').size()
    
    if not monthly_enrollments.empty:
        st.line_chart(monthly_enrollments)
    else:
        st.info("수강신청 추이 데이터가 없습니다.")

def show_material_analytics(db_manager, courses):
    """자료 분석"""
    st.markdown("#### 📚 자료 분석")
    
    material_data = []
    all_documents = []
    
    for course in courses:
        course_id = course['id']
        documents = db_manager.get_course_documents(course_id)
        
        for doc in documents:
            material_data.append({
                '강의명': course['name'],
                '파일명': doc['original_filename'],
                '파일 크기(KB)': doc['file_size'] / 1024,
                '파일 유형': doc['file_type'],
                '업로드일': doc['uploaded_at'],
                '처리 상태': '완료' if doc['is_processed'] else '대기',
                '벡터화 상태': '완료' if doc['is_vectorized'] else '대기'
            })
            all_documents.append(doc)
    
    if not material_data:
        st.info("자료 데이터가 없습니다.")
        return
    
    # 자료 현황 메트릭
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 자료 수", f"{len(all_documents)}개")
    
    with col2:
        processed_docs = len([d for d in all_documents if d['is_processed']])
        st.metric("처리 완료 자료", f"{processed_docs}개")
    
    with col3:
        vectorized_docs = len([d for d in all_documents if d['is_vectorized']])
        st.metric("벡터화 완료 자료", f"{vectorized_docs}개")
    
    with col4:
        total_size = sum(d['file_size'] for d in all_documents) / (1024 * 1024)  # MB
        st.metric("총 파일 크기", f"{total_size:.1f}MB")
    
    # 자료 목록
    st.markdown("#### 📋 업로드된 자료 목록")
    df_materials = pd.DataFrame(material_data)
    st.dataframe(df_materials, use_container_width=True)
    
    # 파일 유형별 분포
    st.markdown("#### 📊 파일 유형별 분포")
    
    file_types = df_materials['파일 유형'].value_counts()
    if not file_types.empty:
        st.bar_chart(file_types)
    else:
        st.info("파일 유형 데이터가 없습니다.")

def show_instructor_detailed_reports(db_manager, courses):
    """교수자 상세 리포트"""
    st.markdown("#### 🔍 상세 리포트")
    
    # 강의 선택
    course_options = {f"{course['name']} ({course['code']})": course['id'] for course in courses}
    selected_course = st.selectbox("분석할 강의를 선택하세요:", list(course_options.keys()))
    
    if selected_course:
        course_id = course_options[selected_course]
        selected_course_data = next(c for c in courses if c['id'] == course_id)
        
        # 선택된 강의 상세 분석
        st.markdown(f"### 📊 {selected_course_data['name']} 상세 분석")
        
        # 기본 정보
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📚 강의 정보")
            st.write(f"**강의명:** {selected_course_data['name']}")
            st.write(f"**강의코드:** {selected_course_data['code']}")
            st.write(f"**학기:** {selected_course_data['semester']}")
            st.write(f"**학점:** {selected_course_data['credit']}")
            st.write(f"**개설일:** {selected_course_data['created_at']}")
        
        with col2:
            # 현재 통계
            enrollments = db_manager.get_course_enrollments(course_id)
            documents = db_manager.get_course_documents(course_id)
            
            st.markdown("#### 📈 현재 통계")
            st.write(f"**수강생:** {len(enrollments)}/{selected_course_data['max_students']}명")
            st.write(f"**자료 수:** {len(documents)}개")
            st.write(f"**등록률:** {(len(enrollments)/selected_course_data['max_students']*100):.1f}%")
        
        # 수강생 상세 목록
        if enrollments:
            st.markdown("#### 👥 수강생 목록")
            students_df = pd.DataFrame([{
                '이름': e['name'],
                '수강신청일': e['enrolled_at'],
                '상태': e['status']
            } for e in enrollments])
            st.dataframe(students_df, use_container_width=True)
        
        # 자료 상세 목록
        if documents:
            st.markdown("#### 📚 자료 목록")
            docs_df = pd.DataFrame([{
                '파일명': d['original_filename'],
                '크기(KB)': d['file_size'] / 1024,
                '유형': d['file_type'],
                '업로드일': d['uploaded_at'],
                '처리 상태': '완료' if d['is_processed'] else '대기'
            } for d in documents])
            st.dataframe(docs_df, use_container_width=True)

def show_system_analytics():
    """시스템 분석 (관리자용)"""
    st.markdown("#### 📈 시스템 사용 현황")
    st.info("🚧 관리자 전용 시스템 분석 기능은 개발 중입니다.")

def show_user_analytics():
    """사용자 분석"""
    st.markdown("#### 👥 사용자 분석")
    
    # 사용자 유형별 분석
    user_types = pd.DataFrame({
        '사용자 유형': ['학습자', '교수자', '관리자'],
        '사용자 수': [180, 25, 5],
        '활성 사용자': [145, 22, 4],
        '평균 세션 시간': ['25분', '45분', '30분']
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 👤 사용자 유형별 현황")
        st.dataframe(user_types, use_container_width=True)
    
    with col2:
        st.markdown("##### 📊 사용자 분포")
        # 파이 차트 데이터
        chart_data = pd.DataFrame({
            'count': user_types['사용자 수'].values,
            'labels': user_types['사용자 유형'].values
        })
        st.bar_chart(chart_data.set_index('labels')['count'])
    
    # 활동 패턴 분석
    st.markdown("##### 🕐 시간대별 활동 패턴")
    
    # 시간대별 더미 데이터
    hours = list(range(0, 24))
    activity_data = pd.DataFrame({
        'hour': hours,
        'activity': [5, 2, 1, 1, 2, 8, 15, 25, 35, 45, 60, 70, 
                    75, 80, 85, 90, 85, 80, 75, 60, 45, 30, 20, 10]
    })
    
    st.line_chart(activity_data.set_index('hour')['activity'])

def show_learning_analytics():
    """학습 분석"""
    st.markdown("#### 📚 학습 분석")
    
    # 학습 성과 지표
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("완료된 과제", "245개", "↗️ 12%")
        st.metric("평균 학습 시간", "2.3시간", "↗️ 18%")
    
    with col2:
        st.metric("생성된 노트", "158개", "↗️ 25%")
        st.metric("AI 도구 사용", "892회", "↗️ 35%")
    
    with col3:
        st.metric("질문 해결률", "87%", "↗️ 5%")
        st.metric("만족도 점수", "4.2/5", "↗️ 0.3")
    
    # 학습 주제별 분석
    st.markdown("##### 📖 인기 학습 주제")
    
    topics_data = pd.DataFrame({
        '주제': ['Python 기초', '데이터 구조', '알고리즘', '웹 개발', '머신러닝'],
        '질문 수': [85, 72, 68, 45, 32],
        '평균 난이도': [3.2, 4.1, 4.5, 3.8, 4.7]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.dataframe(topics_data, use_container_width=True)
    
    with col2:
        st.bar_chart(topics_data.set_index('주제')['질문 수'])

def show_detailed_reports():
    """상세 리포트"""
    st.markdown("#### 🔍 상세 리포트")
    
    # 리포트 유형 선택
    report_type = st.selectbox(
        "리포트 유형을 선택하세요:",
        ["일일 리포트", "주간 리포트", "월간 리포트", "사용자 개별 리포트"]
    )
    
    # 날짜 범위 선택
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("시작 날짜", value=datetime.now() - timedelta(days=7))
    
    with col2:
        end_date = st.date_input("종료 날짜", value=datetime.now())
    
    # 리포트 생성 버튼
    if st.button("📊 리포트 생성", use_container_width=True):
        with st.spinner("리포트 생성 중..."):
            generate_report(report_type, start_date, end_date)

def generate_report(report_type, start_date, end_date):
    """리포트 생성"""
    st.success("✅ 리포트가 성공적으로 생성되었습니다!")
    
    # 더미 리포트 데이터
    st.markdown(f"### 📄 {report_type}")
    st.markdown(f"**기간:** {start_date} ~ {end_date}")
    
    # 요약 정보
    summary_data = {
        "총 사용자": "456명",
        "총 질문": "1,234개",
        "파일 업로드": "89개",
        "평균 응답 시간": "2.3초",
        "시스템 가동률": "99.8%"
    }
    
    st.markdown("#### 📋 요약 정보")
    
    cols = st.columns(len(summary_data))
    for i, (key, value) in enumerate(summary_data.items()):
        with cols[i]:
            st.metric(key, value)
    
    # 상세 데이터 테이블
    st.markdown("#### 📊 상세 데이터")
    
    detailed_data = pd.DataFrame({
        '날짜': pd.date_range(start=start_date, end=end_date, freq='D'),
        '사용자 수': np.random.randint(50, 150, (end_date - start_date).days + 1),
        '질문 수': np.random.randint(100, 300, (end_date - start_date).days + 1),
        '파일 수': np.random.randint(10, 30, (end_date - start_date).days + 1)
    })
    
    st.dataframe(detailed_data, use_container_width=True)
    
    # 다운로드 옵션
    st.markdown("#### 💾 다운로드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Excel 다운로드", use_container_width=True):
            st.info("Phase 2에서 Excel 다운로드 기능이 추가될 예정입니다.")
    
    with col2:
        if st.button("📄 PDF 다운로드", use_container_width=True):
            st.info("Phase 2에서 PDF 다운로드 기능이 추가될 예정입니다.") 