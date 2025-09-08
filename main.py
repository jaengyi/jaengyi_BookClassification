import os
import pandas as pd
from pathlib import Path
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import sys
import io

# UnicodeEncodeError 방지를 위해 stdout/stderr 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')


# 사용자의 홈 디렉토리를 기준으로 절대 경로 설정
HOME = Path.home()
EBOOK_PATH = HOME / "OneDrive/02.eBook"
LIBRARY_FILE = "library.xlsx"

def clean_filename(filename):
    """파일명에서 불필요한 부분을 제거하고 제목과 저자를 분리합니다."""
    # 괄호와 그 안의 내용 제거
    cleaned_name = re.sub(r'\s*\([^)]*\)', '', filename).strip()
    
    # 마지막 단어를 저자로 가정 (일반적인 '제목 저자' 형식)
    parts = cleaned_name.rsplit(' ', 1)
    if len(parts) > 1:
        title = parts[0].strip()
        author = parts[1].strip()
        # 저자 이름으로 보기 어려운 경우 (예: 숫자로만 구성) 다시 합침
        if author.isdigit() or len(author) < 2:
            return cleaned_name, ''
        return title, author

    return cleaned_name, ''

def _extract_toc_recursively(toc_items, level=0):
    """ebooklib의 중첩된 toc를 재귀적으로 파싱하여 문자열로 만듭니다."""
    toc_list = []
    for item in toc_items:
        if isinstance(item, tuple):
            # item is a nested tuple: (Link, (sub-link1, sub-link2, ...))
            link, children = item
            toc_list.append("  " * level + f"- {link.title}")
            toc_list.extend(_extract_toc_recursively(children, level + 1))
        else:
            # item is a Link
            toc_list.append("  " * level + f"- {item.title}")
    return toc_list

def extract_epub_data(file_path):
    """EPUB 파일에서 목차와 서문을 추출합니다."""
    book = epub.read_epub(file_path)
    toc = []
    preface = ""

    # 1. 목차 추출 (중첩 구조 처리)
    toc_list = _extract_toc_recursively(book.toc)
    toc_text = "\n".join(toc_list)

    # 2. 서문 추출 (키워드 기반)
    preface_keywords = ['서문', '머리말', '프롤로그', '시작하며']
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        content = item.get_content()
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # 키워드가 제목이나 초반부에 있는지 확인
        for keyword in preface_keywords:
            if keyword in item.get_name() or keyword in text[:200]:
                preface = text
                break
        if preface:
            break
            
    return toc_text, preface[:1000] # 서문은 1000자까지로 제한

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

def main():
    """메인 실행 함수"""
    print("프로그램을 시작합니다.")
    
    df = pd.DataFrame()
    processed_files = []
    if os.path.exists(LIBRARY_FILE):
        print(f"기존 라이브러리 파일을 로드합니다: {LIBRARY_FILE}")
        df = pd.read_excel(LIBRARY_FILE, dtype={'filepath': str})
        processed_files = df['filepath'].dropna().tolist()
        print(f"총 {len(processed_files)}권의 처리된 도서 정보를 확인했습니다.")
    else:
        print("기존 라이브러리 파일이 없어 새로 시작합니다.")
        df = pd.DataFrame(columns=['filepath', 'title', 'author', 'type', 'toc', 'preface'])

    new_books = scan_new_books(processed_files)

    if not new_books:
        print("새로 추가된 책이 없습니다.")
    else:
        print(f"총 {len(new_books)}권의 새로운 책을 발견했습니다. 정보를 처리합니다.")
        new_data = []
        for book_path_str in new_books:
            book_path = Path(book_path_str)
            filename_stem = book_path.stem
            file_type = book_path.suffix.lower()
            
            title, author = clean_filename(filename_stem)
            toc, preface = "", ""

            print(f"처리 중: {book_path.name}")
            try:
                if file_type == '.epub':
                    toc, preface = extract_epub_data(book_path_str)
                # elif file_type == '.pdf':
                #     # TODO: PDF 처리 함수 추가
                #     pass
                # elif file_type == '.txt':
                #     # TODO: TXT 처리 함수 추가
                #     pass
            except Exception as e:
                print(f"  >> 오류: {book_path.name} 처리 중 오류 발생 - {e}")

            new_data.append({
                'filepath': book_path_str,
                'title': title,
                'author': author,
                'type': file_type,
                'toc': toc,
                'preface': preface
            })
        
        new_df = pd.DataFrame(new_data)
        df = pd.concat([df, new_df], ignore_index=True)
        
        try:
            df.to_excel(LIBRARY_FILE, index=False, engine='openpyxl')
            print(f"성공적으로 {len(new_books)}권의 신규 도서 정보를 {LIBRARY_FILE}에 업데이트했습니다.")
        except Exception as e:
            print(f"파일 저장 중 오류가 발생했습니다: {e}")

    print("프로그램을 종료합니다.")

if __name__ == "__main__":
    main()
