import streamlit as st
from streamlit_option_menu import option_menu

def get_student_menu():
    """학습자 메뉴 반환"""
    return option_menu(
        menu_title=None,
        options=["🏠 홈", "📚 내 강의", "🏛️ 강의실", "📝 학습노트", "🎨 AI도구"],
        icons=["house", "book", "building", "journal-text", "palette"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )

def get_instructor_menu():
    """교수자 메뉴 반환"""
    return option_menu(
        menu_title=None,
        options=["🏠 홈", "📚 강의 관리", "🏛️ 강의실", "📊 수업분석"],
        icons=["house", "book", "building", "bar-chart", "gear"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )

def get_admin_menu():
    """관리자 메뉴 반환"""
    return option_menu(
        menu_title=None,
        options=["🏠 홈", "📊 시스템현황", "👥 사용자관리", "📈 통계분석", "⚙️ 시스템설정"],
        icons=["house", "speedometer2", "people", "graph-up", "sliders"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    ) 