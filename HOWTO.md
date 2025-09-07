# HOWTO: 나만의 디지털 도서관 구축 가이드

이 문서는 Python을 사용하여 지정된 폴더의 전자책을 분석하고, 웹 서평을 수집하여 도서 목록을 만드는 프로그램의 개발 단계를 설명합니다.

## 1. 개발 환경 설정

- **사용 언어:** Python 3.x
- **필요 라이브러리:**
    - `os`, `pathlib`: 파일 및 디렉토리 관리를 위해 사용합니다.
    - `pandas`: 데이터를 표(DataFrame) 형태로 관리하고 Excel/CSV 파일로 저장하기 위해 사용합니다.
    - `EbookLib`: `.epub` 파일의 내용을 읽고 메타데이터를 추출하기 위해 사용합니다.
    - `PyMuPDF` (또는 `pdfplumber`): `.pdf` 파일의 텍스트를 추출하기 위해 사용합니다.
    - `requests`, `BeautifulSoup4`: 웹 페이지의 HTML을 가져오고 파싱하여 서평을 추출하기 위해 사용합니다.
    - `googlesearch-python`: 구글 검색 결과를 프로그래밍적으로 얻기 위해 사용합니다.

- **라이브러리 설치:**
  ```bash
  pip install pandas EbookLib PyMuPDF requests beautifulsoup4 googlesearch-python
  ```

## 2. 프로그램 개발 단계

### 1단계: 도서 파일 스캔 및 목록 관리

1.  **대상 폴더 설정:** 스캔할 전자책 폴더 경로 (`/Users/hyoungwook.oh/OneDrive/02.eBook`)를 변수로 지정합니다.
2.  **기존 목록 로드:** 프로그램 실행 시, 이미 생성된 도서 목록(`library.csv`)이 있다면 `pandas`로 불러옵니다. 없다면 새로운 DataFrame을 생성합니다.
3.  **신규 파일 탐색:** 대상 폴더를 순회하며 `.epub`, `.pdf`, `.txt` 확장자를 가진 파일 목록을 가져옵니다. 이 목록을 기존에 처리된 파일 목록과 비교하여 새로 추가된 파일만 처리 대상으로 선정합니다.

### 2단계: 전자책 내용 추출

각 파일 형식에 맞는 라이브러리를 사용하여 내부 텍스트를 추출하는 함수를 구현합니다.

1.  **EPUB 파일 처리 (`.epub`):**
    - `EbookLib`를 사용하여 EPUB 파일을 엽니다.
    - 책의 메타데이터(저자 등)를 추출합니다.
    - 책의 본문(item)들을 순회하며 텍스트를 추출합니다.
    - "서문", "머리말", "프롤로그", "목차", "차례" 등의 키워드를 기준으로 해당 부분을 식별하고 내용을 저장합니다.

2.  **PDF 파일 처리 (`.pdf`):**
    - `PyMuPDF`를 사용하여 PDF 파일을 엽니다.
    - 페이지를 순회하며 텍스트를 추출합니다.
    - EPUB과 마찬가지로 키워드 검색을 통해 서문, 목차 등의 내용을 찾습니다. PDF는 구조가 복잡하여 텍스트 추출이 완벽하지 않을 수 있습니다.

3.  **TEXT 파일 처리 (`.txt`):**
    - Python의 기본 파일 읽기 기능으로 전체 텍스트를 불러옵니다.
    - 키워드 검색으로 필요한 부분을 추출합니다.

### 3단계: 웹 서평 검색 및 수집

1.  **검색어 생성:** 파일명에서 추출한 '책 제목'과 2단계에서 얻은 '저자' 정보를 조합하여 검색어(예: `"책제목 저자 서평"`)를 만듭니다.
2.  **Google 검색:** `googlesearch` 라이브러리를 사용하여 검색을 수행하고 상위 검색 결과 URL 목록을 얻습니다.
3.  **웹 스크래핑:**
    - `requests`로 각 URL의 HTML을 가져옵니다.
    - `BeautifulSoup4`로 HTML을 파싱하여 블로그 포스트 본문이나 리뷰 내용을 추출합니다.
    - 여러 웹사이트의 구조가 다르므로, 일반적인 텍스트 추출 로직을 구현하고 예외 처리를 포함합니다.
    - 추출된 서평들 중 의미 있는 내용을 요약하거나 일부를 발췌하여 저장합니다.

### 4단계: 데이터 종합 및 저장

1.  **데이터 구조화:** 스캔 및 추출된 모든 정보(파일 경로, 제목, 저자, 파일 타입, 서문, 목차, 서평 요약)를 `pandas` DataFrame의 한 행으로 구성합니다.
2.  **목록 업데이트:** 1단계에서 불러온 기존 DataFrame에 새로운 책의 정보를 추가(`append`)합니다.
3.  **파일로 저장:** 최종 업데이트된 DataFrame을 `library.csv` 또는 `library.xlsx` 파일로 저장합니다. `to_csv` 또는 `to_excel` 메소드를 사용하며, 인코딩은 `utf-8-sig`로 설정하여 한글 깨짐을 방지합니다.

## 3. 최종 실행 스크립트 구조 (예시)

```python
import os
import pandas as pd
# ... 다른 라이브러리 import

EBOOK_PATH = "/Users/hyoungwook.oh/OneDrive/02.eBook"
LIBRARY_FILE = "library.csv"

def scan_new_books(processed_files):
    # EBOOK_PATH에서 새 책 파일 목록 반환
    pass

def extract_epub_data(file_path):
    # epub에서 서문, 목차 등 추출
    pass

def extract_pdf_data(file_path):
    # pdf에서 서문, 목차 등 추출
    pass

def search_reviews_online(title, author):
    # 웹에서 서평 검색 및 요약
    pass

def main():
    # 1. 기존 라이브러리 파일 로드
    try:
        df = pd.read_csv(LIBRARY_FILE)
        processed_files = df['filepath'].tolist()
    except FileNotFoundError:
        df = pd.DataFrame(columns=['filepath', 'title', 'author', 'type', 'preface', 'toc', 'reviews'])
        processed_files = []

    # 2. 신규 도서 스캔
    new_books = scan_new_books(processed_files)

    # 3. 각 신규 도서 정보 추출 및 처리
    for book_path in new_books:
        # 파일 타입에 따라 정보 추출
        # ...
        
        # 웹 서평 검색
        # ...

        # DataFrame에 추가
        # ...

    # 4. 최종 결과를 CSV 파일에 저장
    df.to_csv(LIBRARY_FILE, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    main()
```
