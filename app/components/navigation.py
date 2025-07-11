import streamlit as st
from streamlit_option_menu import option_menu

def get_student_menu():
    """학습자 메뉴 반환"""
    return option_menu(
        menu_title=None,
        options=["🏠 홈", "📚 내 강의", "📝 학습노트"],
        icons=["house", "book", "journal-text"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )

def get_instructor_menu():
    """교수자 메뉴 반환"""
    return option_menu(
        menu_title=None,
        options=["🏠 홈", "📚 강의 관리", "📊 수업분석"],
        icons=["house", "book", "bar-chart"],
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