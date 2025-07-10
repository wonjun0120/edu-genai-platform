import streamlit as st
from pathlib import Path
from datetime import datetime
import pandas as pd
import math

def handle_file_upload(uploaded_files, folder_name="uploads"):
    """파일 업로드 처리"""
    if uploaded_files:
        # uploads 폴더 생성
        upload_dir = Path(folder_name)
        upload_dir.mkdir(exist_ok=True)
        
        saved_files = []
        for uploaded_file in uploaded_files:
            # 파일 저장
            file_path = upload_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 파일 정보 저장
            file_info = {
                "name": uploaded_file.name,
                "size": uploaded_file.size,
                "type": uploaded_file.type,
                "path": str(file_path),
                "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            saved_files.append(file_info)
            
            # 세션에 파일 정보 저장
            if file_info not in st.session_state.uploaded_files:
                st.session_state.uploaded_files.append(file_info)
        
        return saved_files
    return []

def get_uploaded_files():
    """업로드된 파일 목록 반환"""
    return st.session_state.get('uploaded_files', [])

def format_file_size(size_bytes):
    """파일 크기를 읽기 좋은 형태로 포맷팅"""
    if size_bytes == 0:
        return "0B"
    size_name = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}" 