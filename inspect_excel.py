import pandas as pd

try:
    df = pd.read_excel("library.xlsx")
    print(df.head())
except FileNotFoundError:
    print("library.xlsx 파일을 찾을 수 없습니다.")
except Exception as e:
    print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
