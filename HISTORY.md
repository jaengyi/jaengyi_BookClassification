# 작업 기록

## 2025-09-08

### 1. 초기 스크립트 분석 및 오류 수정
- `requirements.txt` 의존성 설치 및 `main.py` 최초 실행.
- 실행 시 발생하는 `UnicodeEncodeError` (Windows 환경 인코딩 문제) 및 `AttributeError` (EPUB 목차 파싱 문제) 식별.
- `main.py`를 수정하여 표준 출력 인코딩을 UTF-8로 설정하고, 중첩된 EPUB 목차 구조를 재귀적으로 탐색하도록 로직을 개선하여 오류 해결.

### 2. 도서 분류 기능 및 데이터베이스 연동 (Phase 1)
- **도서 분류 기능 추가**: `main.py`에 제목과 목차 키워드를 기반으로 도서를 'IT/프로그래밍', '자기계발', '경제/경영', '소설', '기타'로 자동 분류하는 `classify_book` 함수 구현.
- **데이터 저장소 변경**: 기존의 Excel 파일(`library.xlsx`) 저장 방식에서 PostgreSQL 데이터베이스에 저장하는 방식으로 변경.
- **Docker 기반 DB 환경 구축**: `docker-compose.yml` 파일을 작성하여 PostgreSQL 데이터베이스 서버를 컨테이너 환경으로 구축. `docker-compose up -d` 명령어로 DB 서버 실행.
- **DB 연동 라이브러리 추가**: `requirements.txt`에 `psycopg2-binary` (PostgreSQL 드라이버)와 `SQLAlchemy` (ORM) 추가 및 설치.
- **데이터베이스 마이그레이션**: `main.py` 스크립트를 실행하여 로컬 도서 파일을 스캔 및 분류하고, 그 결과를 Docker의 PostgreSQL 데이터베이스에 성공적으로 저장.
