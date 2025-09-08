import os
import pandas as pd
from pathlib import Path
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import sys
import io
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import time

# --- Configuration ---
# UnicodeEncodeError 방지를 위해 stdout/stderr 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

# 경로 설정
HOME = Path.home()
EBOOK_PATH = HOME / "OneDrive/02.eBook"

# 데이터베이스 설정 (환경 변수 사용)
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "book_library")
DB_TABLE = "books"
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- Functions ---

def classify_book(title, toc, filepath):
    """책 제목, 목차, 파일 경로를 기반으로 카테고리를 분류합니다."""
    title_toc = (title + " " + toc).lower()
    filepath_str = str(filepath).lower()

    # IT/프로그래밍 키워드
    it_keywords = [
        'python', 'java', 'javascript', 'c#', 'c++', 'sql', 'database', 'server',
        'network', 'security', 'hacking', 'linux', 'aws', 'docker', 'kubernetes',
        'react', 'vue', 'angular', 'spring', 'django', 'flask', 'coding', 'it',
        '프로그래밍', '코딩', '개발자', '서버', '데이터베이스', '보안', '해킹'
    ]
    if any(keyword in title_toc or keyword in filepath_str for keyword in it_keywords):
        return 'IT/프로그래밍'

    # 자기계발 키워드
    dev_keywords = [
        '습관', '성공', '부자', '성장', '심리', '마음', '자존감', '자기계발',
        '부의', '성품', '인생', '변화', '성장', '성품'
    ]
    if any(keyword in title_toc for keyword in dev_keywords):
        return '자기계발'

    # 경제/경영 키워드
    econ_keywords = [
        '경제', '경영', '투자', '주식', '부동산', '돈', '재테크', '마케팅', '비즈니스'
    ]
    if any(keyword in title_toc for keyword in econ_keywords):
        return '경제/경영'
        
    # 소설/문학 키워드
    novel_keywords = [
        '소설', '문학', '시', '에세이', '이야기'
    ]
    if any(keyword in title_toc for keyword in novel_keywords):
        return '소설/문학'

    return '기타'


def clean_filename(filename):
    """파일명에서 불필요한 부분을 제거하고 제목과 저자를 분리합니다."""
    cleaned_name = re.sub(r'\s*\([^)]*\)', '', filename).strip()
    parts = cleaned_name.rsplit(' ', 1)
    if len(parts) > 1:
        title, author = parts[0].strip(), parts[1].strip()
        if author.isdigit() or len(author) < 2:
            return cleaned_name, ''
        return title, author
    return cleaned_name, ''

def _extract_toc_recursively(toc_items, level=0):
    """ebooklib의 중첩된 toc를 재귀적으로 파싱하여 문자열로 만듭니다."""
    toc_list = []
    for item in toc_items:
        if isinstance(item, tuple):
            link, children = item
            toc_list.append("  " * level + f"- {link.title}")
            toc_list.extend(_extract_toc_recursively(children, level + 1))
        else:
            toc_list.append("  " * level + f"- {item.title}")
    return toc_list

def extract_epub_data(file_path):
    """EPUB 파일에서 목차와 서문을 추출합니다."""
    book = epub.read_epub(file_path)
    preface = ""

    toc_list = _extract_toc_recursively(book.toc)
    toc_text = "\n".join(toc_list)

    preface_keywords = ['서문', '머리말', '프롤로그', '시작하며']
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        content = item.get_content()
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        for keyword in preface_keywords:
            if keyword in item.get_name() or keyword in text[:200]:
                preface = text
                break
        if preface:
            break
    return toc_text, preface[:1000]

def scan_new_books(processed_files):
    """지정된 경로에서 아직 처리되지 않은 새 책 파일 목록을 찾습니다."""
    new_books = []
    supported_extensions = ['.epub', '.pdf', '.txt']
    if not EBOOK_PATH.exists():
        print(f"오류: 지정된 eBook 경로를 찾을 수 없습니다: {EBOOK_PATH}")
        return []
    print(f"도서 스캔 시작: {EBOOK_PATH}")
    for filepath in EBOOK_PATH.rglob('*'):
        if filepath.suffix.lower() in supported_extensions:
            if str(filepath) not in processed_files:
                new_books.append(str(filepath))
    return new_books

def get_db_engine():
    """데이터베이스 엔진을 생성하고 반환합니다."""
    for i in range(5): # 5번 재시도
        try:
            engine = create_engine(DB_URL)
            with engine.connect() as connection:
                print("데이터베이스 연결 성공!")
                return engine
        except OperationalError as e:
            print(f"DB 연결 실패 ({i+1}/5): {e}. 5초 후 재시도합니다.")
            time.sleep(5)
    print("오류: 데이터베이스에 연결할 수 없습니다.")
    return None

def main():
    """메인 실행 함수"""
    print("프로그램을 시작합니다.")
    
    engine = get_db_engine()
    if not engine:
        return

    processed_files = []
    try:
        with engine.connect() as connection:
            # 테이블이 없으면 생성
            connection.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {DB_TABLE} (
                id SERIAL PRIMARY KEY,
                filepath TEXT UNIQUE NOT NULL,
                title TEXT,
                author TEXT,
                category VARCHAR(50),
                type VARCHAR(10),
                toc TEXT,
                preface TEXT
            );
            """))
            connection.commit()
            
            # 기존 파일 목록 로드
            result = connection.execute(text(f"SELECT filepath FROM {DB_TABLE}"))
            processed_files = [row[0] for row in result]
            print(f"총 {len(processed_files)}권의 처리된 도서 정보를 DB에서 확인했습니다.")

    except Exception as e:
        print(f"데이터베이스 초기화 중 오류 발생: {e}")
        return

    new_books = scan_new_books(processed_files)

    if not new_books:
        print("새로 추가된 책이 없습니다.")
    else:
        print(f"총 {len(new_books)}권의 새로운 책을 발견했습니다. 정보를 처리합니다.")
        new_data = []
        for book_path_str in new_books:
            book_path = Path(book_path_str)
            print(f"처리 중: {book_path.name}")
            
            title, author = clean_filename(book_path.stem)
            toc, preface = "", ""
            
            try:
                if book_path.suffix.lower() == '.epub':
                    toc, preface = extract_epub_data(book_path_str)
            except Exception as e:
                print(f"  >> 오류: {book_path.name} 처리 중 오류 발생 - {e}")

            category = classify_book(title, toc, book_path)

            new_data.append({
                'filepath': book_path_str,
                'title': title,
                'author': author,
                'category': category,
                'type': book_path.suffix.lower(),
                'toc': toc,
                'preface': preface
            })
        
        if new_data:
            new_df = pd.DataFrame(new_data)
            try:
                new_df.to_sql(DB_TABLE, engine, if_exists='append', index=False)
                print(f"성공적으로 {len(new_data)}권의 신규 도서 정보를 DB에 업데이트했습니다.")
            except Exception as e:
                print(f"DB 저장 중 오류가 발생했습니다: {e}")

    print("프로그램을 종료합니다.")

if __name__ == "__main__":
    main()

