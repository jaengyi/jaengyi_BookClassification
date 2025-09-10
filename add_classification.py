import pandas as pd
from pathlib import Path
import re

def classify_book(title, toc, filepath):
    """책 제목, 목차, 파일 경로를 기반으로 카테고리를 분류합니다."""
    # toc가 NaN일 경우 빈 문자열로 처리
    if pd.isna(toc):
        toc = ""
        
    title_toc = (str(title) + " " + str(toc)).lower()
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
    # Path 객체일 경우 stem으로 파일 이름을 가져옴
    if isinstance(filename, Path):
        filename = filename.stem
    cleaned_name = re.sub(r'\s*\([^)]*\)', '', filename).strip()
    parts = cleaned_name.rsplit(' ', 1)
    if len(parts) > 1:
        title, author = parts[0].strip(), parts[1].strip()
        if author.isdigit() or len(author) < 2:
            return cleaned_name, ''
        return title, author
    return cleaned_name, ''

try:
    # 엑셀 파일 읽기
    df = pd.read_excel("library.xlsx")
    print("기존 library.xlsx 파일을 읽었습니다.")

    # 'title'과 'toc' 열이 없는 경우를 대비하여 초기화
    if 'title' not in df.columns:
        df['title'] = ''
    if 'toc' not in df.columns:
        df['toc'] = ''
    if 'author' not in df.columns:
        df['author'] = ''

    # 제목과 저자 추출
    for index, row in df.iterrows():
        path = Path(row['filepath'])
        title, author = clean_filename(path.stem)
        df.at[index, 'title'] = title
        df.at[index, 'author'] = author

    # 카테고리 분류
    df['category'] = df.apply(lambda row: classify_book(row['title'], row.get('toc', ''), row['filepath']), axis=1)
    print("분류 작업을 완료했습니다.")

    # 업데이트된 데이터프레임을 새 엑셀 파일로 저장
    df.to_excel("library_with_classification.xlsx", index=False)
    print("분류가 추가된 'library_with_classification.xlsx' 파일을 저장했습니다.")

except FileNotFoundError:
    print("library.xlsx 파일을 찾을 수 없습니다.")
except Exception as e:
    print(f"작업 중 오류가 발생했습니다: {e}")
