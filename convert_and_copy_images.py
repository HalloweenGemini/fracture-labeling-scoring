import os
from PIL import Image
import glob
import shutil

def convert_to_webp(source_path, destination_path):
    """PNG 이미지를 WebP로 변환"""
    try:
        # WebP 파일 경로 생성
        webp_path = os.path.splitext(destination_path)[0] + '.webp'
        
        # 이미 WebP 파일이 존재하면 건너뛰기
        if os.path.exists(webp_path):
            return webp_path
            
        image = Image.open(source_path)
        # WebP로 변환하여 저장
        image.save(webp_path, 'WEBP', quality=90)
        print(f"Converted: {source_path} -> {webp_path}")
        return webp_path
    except Exception as e:
        print(f"Error converting {source_path}: {e}")
        # 변환 실패 시 원본 파일 복사 (이미 존재하지 않는 경우에만)
        if not os.path.exists(destination_path):
            shutil.copy2(source_path, destination_path)
            print(f"Copied original: {source_path} -> {destination_path}")
        return destination_path

def setup_image_serving():
    """이미지 서빙을 위한 설정"""
    # 소스 및 대상 디렉토리 설정
    source_dir = "Pilot_wrist_0615/Test/images"
    static_dir = "static/images"
    
    # static/images 디렉토리 생성
    os.makedirs(static_dir, exist_ok=True)
    
    # 변환 상태 파일 확인
    status_file = os.path.join(static_dir, '.conversion_complete')
    if os.path.exists(status_file):
        return  # 이미 변환이 완료된 경우 종료
    
    # PNG 파일 찾기
    png_files = glob.glob(os.path.join(source_dir, "*.png"))
    
    # 각 이미지 처리
    for png_file in png_files:
        filename = os.path.basename(png_file)
        destination = os.path.join(static_dir, filename)
        convert_to_webp(png_file, destination)
    
    # 변환 완료 표시
    with open(status_file, 'w') as f:
        f.write('done')

if __name__ == "__main__":
    setup_image_serving() 