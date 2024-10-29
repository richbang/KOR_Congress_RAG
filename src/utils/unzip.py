import zipfile
import os
import re

def safe_filename(filename):
    return re.sub(r'\W+', '_', filename)

# 압축해제 함수
def unzip_kor(zip_file_path, extraction_path):
    os.makedirs(extraction_path, exist_ok=True)
    idx = 0
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        for index, member in enumerate(zip_ref.infolist()):
            original_name = member.filename
            safe_name = f"file_{idx}.json"
            extracted_path = os.path.join(extraction_path, safe_name)
            with zip_ref.open(member) as source, open(extracted_path, 'wb') as target:
                target.write(source.read())
                idx+=1
    print(f"압축해제 완료: {extraction_path}")

# Training 데이터 중에서 라벨링데이터들의 zip파일의 경로 설정
zip_files = [
    './dataset/TL_국정감사.zip',
    './dataset/TL_본회의.zip',
    './dataset/TL_소위원회.zip',
    './dataset/TL_예산결산특별위원회.zip',
    './dataset/TL_특별위원회.zip'
]

extraction_path = '../dataset/processed/'

# Loop through each ZIP file and extract its contents
for zip_file in zip_files:
    unzip_kor(zip_file, extraction_path)