# =============================================================================
# Makefile for edu-genai-platform
# =============================================================================

.PHONY: help install install-dev clean run-app jupyter test lint format
.DEFAULT_GOAL := help

# Python 관련 설정
PYTHON_VERSION := 3.10
VENV_NAME := venv
PROJECT_DIR := 코멘토-2주차-AI-프로젝트

help: ## 도움말 출력
	@echo "사용 가능한 명령어들:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# =============================================================================
# venv 관련 명령어들 
# =============================================================================

venv-create: ## Python venv 가상환경 생성
	python$(PYTHON_VERSION) -m venv $(VENV_NAME)

venv-activate: ## venv 활성화 (사용법: source venv/bin/activate)
	@echo "가상환경 활성화를 위해 다음 명령어를 실행하세요:"
	@echo "source $(VENV_NAME)/bin/activate"

venv-install: ## venv에서 pip로 의존성 설치
	./$(VENV_NAME)/bin/pip install -r requirements.txt

venv-freeze: ## 현재 설치된 패키지 목록을 requirements.txt로 저장
	./$(VENV_NAME)/bin/pip freeze > requirements.txt

venv-deactivate: ## venv 비활성화
	@echo "가상환경 비활성화를 위해 다음 명령어를 실행하세요:"
	@echo "deactivate"

venv-clean: ## venv 환경 삭제
	rm -rf $(VENV_NAME)

# =============================================================================
# 프로젝트 실행 관련 (venv 기반)
# =============================================================================

install: venv-create venv-install ## 기본 설치 (venv 생성 + 의존성 설치)

install-dev: install ## 개발환경 설치

run-streamlit: ## Streamlit 앱 실행 (venv 환경)
	@test -d $(VENV_NAME) || (echo "venv 환경이 없습니다. 'make install'을 먼저 실행하세요." && exit 1)
	./$(VENV_NAME)/bin/python -m streamlit run $(PROJECT_DIR)/app.py

run-app: run-streamlit ## 앱 실행 (streamlit 별칭)

jupyter: ## Jupyter Notebook 실행 (venv 환경)
	@test -d $(VENV_NAME) || (echo "venv 환경이 없습니다. 'make install'을 먼저 실행하세요." && exit 1)
	./$(VENV_NAME)/bin/jupyter notebook

notebook: jupyter ## Jupyter Notebook 실행 (별칭)

python: ## Python 인터프리터 실행 (venv 환경)
	@test -d $(VENV_NAME) || (echo "venv 환경이 없습니다. 'make install'을 먼저 실행하세요." && exit 1)
	./$(VENV_NAME)/bin/python

run-script: ## Python 스크립트 실행 (예: make run-script SCRIPT=app.py)
	@test -d $(VENV_NAME) || (echo "venv 환경이 없습니다. 'make install'을 먼저 실행하세요." && exit 1)
	./$(VENV_NAME)/bin/python $(SCRIPT)

# =============================================================================
# 프론트엔드 관련
# =============================================================================

npm-install: ## npm 의존성 설치
	cd $(PROJECT_DIR) && npm install

npm-update: ## npm 패키지 업데이트
	cd $(PROJECT_DIR) && npm update

# =============================================================================
# 개발 도구 (venv 기반)
# =============================================================================

lint: ## 코드 린팅
	@test -d $(VENV_NAME) || (echo "venv 환경이 없습니다. 'make install'을 먼저 실행하세요." && exit 1)
	./$(VENV_NAME)/bin/python -m flake8 .

format: ## 코드 포맷팅
	@test -d $(VENV_NAME) || (echo "venv 환경이 없습니다. 'make install'을 먼저 실행하세요." && exit 1)
	./$(VENV_NAME)/bin/python -m black .
	./$(VENV_NAME)/bin/python -m isort .

type-check: ## 타입 체킹
	@test -d $(VENV_NAME) || (echo "venv 환경이 없습니다. 'make install'을 먼저 실행하세요." && exit 1)
	./$(VENV_NAME)/bin/python -m mypy .

pip-upgrade: ## pip 업그레이드
	@test -d $(VENV_NAME) || (echo "venv 환경이 없습니다. 'make install'을 먼저 실행하세요." && exit 1)
	./$(VENV_NAME)/bin/pip install --upgrade pip

requirements-update: ## requirements.txt 업데이트
	@test -d $(VENV_NAME) || (echo "venv 환경이 없습니다. 'make install'을 먼저 실행하세요." && exit 1)
	./$(VENV_NAME)/bin/pip freeze > requirements.txt

# =============================================================================
# 정리 및 유지보수
# =============================================================================

clean: ## 임시 파일들 정리
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".DS_Store" -delete

clean-all: clean venv-clean ## 모든 환경 및 임시 파일 정리

# =============================================================================
# 정보 출력
# =============================================================================

info: ## 프로젝트 정보 출력
	@echo "=== 프로젝트 정보 ==="
	@echo "Python 버전: $(PYTHON_VERSION)"
	@echo "프로젝트 디렉토리: $(PROJECT_DIR)"
	@echo "가상환경 이름: $(VENV_NAME)"
	@echo ""
	@echo "=== venv 상태 ==="
	@test -d $(VENV_NAME) && echo "venv 환경 존재함: $(shell ./$(VENV_NAME)/bin/python --version 2>/dev/null || echo '비활성화')" || echo "venv 환경 없음"
	@test -d $(VENV_NAME) && echo "설치된 패키지 수: $(shell ./$(VENV_NAME)/bin/pip list --format=freeze 2>/dev/null | wc -l || echo '0')" || true
	@echo ""
	@echo "=== requirements.txt 상태 ==="
	@test -f requirements.txt && echo "requirements.txt 존재함" || echo "requirements.txt 없음"

status: info ## 프로젝트 상태 출력 (info 별칭)

# =============================================================================
# 빠른 시작
# =============================================================================

setup: install npm-install ## 초기 설정 (venv + npm)

quick-start: setup run-app ## 빠른 시작 (설치 후 앱 실행)

dev: setup format lint ## 개발 환경 설정 (설치 + 포맷팅 + 린팅)

