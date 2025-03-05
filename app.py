from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import glob
import json
import time
import random
from datetime import datetime
import cv2
from PIL import Image
import pathlib
import logging

app = Flask(__name__)
# 로깅 레벨 조정
app.logger.setLevel(logging.ERROR)  # DEBUG에서 ERROR로 변경

# 타이머 클래스 추가
class Timer:
    def __init__(self):
        self.start_time = time.time()
    
    def reset(self):
        self.start_time = time.time()
    
    def get_elapsed_time(self):
        elapsed_time = int(time.time() - self.start_time)
        minutes = elapsed_time // 60
        seconds = elapsed_time % 60
        return f"{minutes:02d}:{seconds:02d}"

# 고정된 랜덤 시드 설정
RANDOM_SEED = 42

# 세션 데이터를 저장할 전역 변수
class AppState:
    def __init__(self):
        self.start_time = time.time()
        self.current_image_idx = 0
        self.bboxes = {}  # 이미지별 바운딩 박스 저장
        self.selected_id = None
        self.id_image_orders = {}  # ID별 이미지 순서 저장
        self.timer = Timer()

app_state = AppState()

# 폴더 경로 설정 (pathlib 사용)
base_path = pathlib.Path("Pilot_wrist_0615/Test").resolve()
static_images_path = pathlib.Path(app.static_folder) / 'images'  # static 이미지 경로 추가

def get_labels_path(user_id):
    """사용자 ID에 따른 labels 경로 반환"""
    return base_path / f"id{user_id}" / "labels"

def load_bboxes_for_image(image_name, user_id):
    """특정 이미지와 사용자 ID에 대한 바운딩 박스 로드"""
    labels_path = get_labels_path(user_id)
    label_name = pathlib.Path(image_name).stem + '.txt'
    label_path = labels_path / label_name
    
    bboxes = []
    
    if label_path.exists():
        img_path = static_images_path / image_name  # static 이미지 경로 사용
        try:
            # WebP 파일을 PIL로 로드하여 크기 확인
            img = Image.open(str(img_path))
            img_width, img_height = img.size
            
            with open(label_path, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                parts = line.strip().split()
                if len(parts) == 5:
                    class_id = int(parts[0])
                    x_center = float(parts[1]) * img_width
                    y_center = float(parts[2]) * img_height
                    width = float(parts[3]) * img_width
                    height = float(parts[4]) * img_height
                    
                    x = x_center - width / 2
                    y = y_center - height / 2
                    
                    bboxes.append([x, y, width, height, class_id])
        except Exception as e:
            print(f"이미지 로드 오류: {e}")
    
    return bboxes

@app.route('/')
def index():
    # ID 선택 페이지
    return render_template('index.html')

@app.route('/select_id/<int:id>')
def select_id(id):
    app_state.selected_id = id
    app_state.start_time = time.time()  # 기존 타이머 초기화 (legacy)
    app_state.timer.reset()  # 타이머 클래스 초기화
    app_state.current_image_idx = 0  # 이미지 인덱스 초기화
    app_state.bboxes = {}  # ID가 변경되면 바운딩 박스 초기화
    
    # ID별 labels 폴더 생성
    labels_path = get_labels_path(id)
    labels_path.mkdir(parents=True, exist_ok=True)
    
    # 현재 이미지의 바운딩 박스 로드
    image_files = get_image_files()  # WebP 파일만 가져오기
    
    # 각 ID별로 고정된 이미지 순서 생성
    if id not in app_state.id_image_orders:
        # 동일한 시드로 랜덤화하여 항상 같은 순서 유지
        random.seed(RANDOM_SEED + id)  # ID에 따라 시드 변경
        app_state.id_image_orders[id] = random.sample(image_files, len(image_files))
        random.seed()  # 시드 초기화
    
    # 현재 ID의 모든 이미지에 대한 바운딩 박스 미리 로드
    for image_name in app_state.id_image_orders[id]:
        app_state.bboxes[image_name] = load_bboxes_for_image(image_name, id)
    
    return redirect(url_for('main_app'))

def get_image_files():
    """static/images 디렉토리에서 WebP 이미지 파일 목록만 가져오기"""
    static_images_path = pathlib.Path(app.static_folder) / 'images'
    print(f"이미지 디렉토리 경로: {static_images_path}")
    print(f"이미지 디렉토리 존재 여부: {static_images_path.exists()}")
    
    # WebP 파일만 사용
    image_files = list(static_images_path.glob('*.webp'))
    print(f"발견된 WebP 파일 수: {len(image_files)}")
    
    # 파일이 없으면 첫 번째 파일만 출력해 보기
    if image_files:
        print(f"첫 번째 이미지: {image_files[0]}")
    
    return sorted([f.name for f in image_files])

@app.route('/main')
def main_app():
    """메인 라벨링 페이지를 표시합니다."""
    if app_state.selected_id is None:
        return redirect(url_for('index'))
    
    # 현재 이미지 인덱스 확인
    if app_state.current_image_idx >= len(app_state.id_image_orders[app_state.selected_id]):
        app_state.current_image_idx = 0
    
    # 현재 이미지 정보
    current_image = app_state.id_image_orders[app_state.selected_id][app_state.current_image_idx]
    image_path = f"images/{current_image}"
    
    # 이미지 크기 확인 (PIL 사용)
    try:
        img_path = static_images_path / current_image
        print(f"이미지 경로: {image_path}")  
        print(f"이미지 전체 경로: {img_path}")
        print(f"이미지 파일 존재 여부: {img_path.exists()}")
        
        with Image.open(str(img_path)) as img:
            width, height = img.size
            aspect_ratio = width / height
            print(f"이미지 로드 성공: {width}x{height}")
            
            debug_info = {
                'original_size': f"{width}x{height}",
                'aspect_ratio': f"{aspect_ratio:.2f}"
            }
    except Exception as e:
        print(f"이미지 로드 실패: {e}")
        debug_info = {
            'original_size': "알 수 없음",
            'aspect_ratio': "알 수 없음"
        }
    
    # 현재 이미지의 바운딩 박스
    if current_image not in app_state.bboxes:
        app_state.bboxes[current_image] = load_bboxes_for_image(current_image, app_state.selected_id)
    
    current_bboxes = app_state.bboxes.get(current_image, [])
    
    # 모든 이미지의 라벨 상태 확인
    bboxes_status = {}
    for img_name in app_state.id_image_orders[app_state.selected_id]:
        label_name = pathlib.Path(img_name).stem + '.txt'
        label_path = get_labels_path(app_state.selected_id) / label_name
        bboxes_status[img_name] = label_path.exists() and label_path.stat().st_size > 0
    
    # 타이머 값 가져오기
    timer = app_state.timer.get_elapsed_time()
    
    # 라벨링 진행 상황 계산
    labeled_count, total_images, progress_percent = get_labeling_progress(app_state.selected_id)
    
    return render_template(
        'main.html', 
        user_id=app_state.selected_id,
        image_path=image_path,
        image_name=current_image,
        image_list=app_state.id_image_orders[app_state.selected_id],
        current_idx=app_state.current_image_idx,
        bboxes=json.dumps(current_bboxes),
        timer=timer,
        labeled_count=labeled_count,
        total_images=total_images,
        progress_percent=progress_percent,
        bboxes_status=bboxes_status,
        debug_info=debug_info
    )

@app.route('/next_image')
def next_image():
    # 이미지 목록 가져오기
    image_files = app_state.id_image_orders.get(app_state.selected_id, get_image_files())
    
    # 다음 인덱스로 이동
    if app_state.current_image_idx < len(image_files) - 1:
        app_state.current_image_idx += 1
    
    return redirect(url_for('main_app'))

def create_empty_label_if_not_exists(image_name, user_id):
    """라벨 파일이 없는 경우 빈 파일 생성"""
    labels_path = get_labels_path(user_id)
    label_name = pathlib.Path(image_name).stem + '.txt'
    label_path = labels_path / label_name
    
    # 파일이 없는 경우에만 빈 파일 생성
    if not label_path.exists():
        label_path.parent.mkdir(parents=True, exist_ok=True)
        label_path.touch()  # 빈 파일 생성

@app.route('/prev_image')
def prev_image():
    if app_state.current_image_idx > 0:
        app_state.current_image_idx -= 1
    return redirect(url_for('main_app'))

@app.route('/select_image/<int:idx>')
def select_image(idx):
    # 이미지 목록 가져오기
    image_files = app_state.id_image_orders.get(app_state.selected_id, get_image_files())
    
    if 0 <= idx < len(image_files):
        app_state.current_image_idx = idx
    
    return redirect(url_for('main_app'))

@app.route('/save_bbox', methods=['POST'])
def save_bbox():
    if app_state.selected_id is None:
        return jsonify({'status': 'error', 'message': 'User ID is not selected'}), 400
        
    data = request.json
    image_name = data.get('image_name')
    bbox = data.get('bbox')  # [x, y, width, height, class_id]
    
    if not image_name or not bbox:
        return jsonify({'status': 'error', 'message': 'Missing image_name or bbox data'}), 400
    
    if image_name not in app_state.bboxes:
        app_state.bboxes[image_name] = []
    
    app_state.bboxes[image_name].append(bbox)
    
    try:
        # YOLO 형식으로 라벨 저장
        save_yolo_label(image_name, bbox)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def save_yolo_label(image_name, bbox):
    if app_state.selected_id is None:
        raise ValueError("User ID is not selected")
        
    # 실제 이미지 크기 가져오기
    img_path = static_images_path / image_name  # static 이미지 경로 사용
    try:
        # WebP 파일을 PIL로 로드하여 크기 확인
        img = Image.open(str(img_path))
        img_width, img_height = img.size
    except Exception as e:
        raise ValueError(f"Failed to read image: {image_name}. Error: {str(e)}")
    
    x, y, width, height, class_id = bbox
    
    # YOLO 형식으로 변환
    x_center = (x + width/2) / img_width
    y_center = (y + height/2) / img_height
    norm_width = width / img_width
    norm_height = height / img_height
    
    # ID별 labels 폴더에 저장
    labels_path = get_labels_path(app_state.selected_id)
    labels_path.mkdir(parents=True, exist_ok=True)  # 디렉토리가 없는 경우 생성
    
    label_name = pathlib.Path(image_name).stem + '.txt'
    label_path = labels_path / label_name
    
    new_line = f"{class_id} {x_center:.6f} {y_center:.6f} {norm_width:.6f} {norm_height:.6f}\n"
    
    # 기존 라벨이 있으면 추가, 없으면 새로 생성
    with open(label_path, 'a') as f:
        f.write(new_line)

@app.route('/get_timer')
def get_timer():
    """현재 타이머 값을 반환합니다."""
    # 로깅 없이 타이머 값만 반환
    return jsonify({'timer': app_state.timer.get_elapsed_time()})

@app.route('/delete_last_bbox', methods=['POST'])
def delete_last_bbox():
    data = request.json
    image_name = data.get('image_name')
    
    # 메모리에서 삭제
    if image_name in app_state.bboxes and app_state.bboxes[image_name]:
        app_state.bboxes[image_name].pop()
    
    # 파일에서 삭제
    labels_path = get_labels_path(app_state.selected_id)
    label_name = pathlib.Path(image_name).stem + '.txt'
    label_path = labels_path / label_name
    
    if label_path.exists():
        try:
            with open(label_path, 'r') as f:
                lines = f.readlines()
            
            if lines:
                # 마지막 줄 삭제
                lines = lines[:-1]
                
                # 파일 다시 쓰기
                with open(label_path, 'w') as f:
                    f.writelines(lines)
        except Exception as e:
            print(f"파일 처리 오류: {e}")
            return jsonify({'status': 'error', 'message': str(e)})
    
    return jsonify({'status': 'success'})

@app.route('/delete_all_bboxes', methods=['POST'])
def delete_all_bboxes():
    data = request.json
    image_name = data.get('image_name')
    
    # 메모리에서 삭제
    if image_name in app_state.bboxes:
        app_state.bboxes[image_name] = []
    
    # 파일에서 삭제
    labels_path = get_labels_path(app_state.selected_id)
    label_name = pathlib.Path(image_name).stem + '.txt'
    label_path = labels_path / label_name
    
    if label_path.exists():
        try:
            # 파일 비우기
            with open(label_path, 'w') as f:
                pass
        except Exception as e:
            print(f"파일 처리 오류: {e}")
            return jsonify({'status': 'error', 'message': str(e)})
    
    return jsonify({'status': 'success'})

@app.route('/mark_no_fracture', methods=['POST'])
def mark_no_fracture():
    """특정 이미지에 대해 No Fracture 라벨을 생성합니다. (빈 파일 생성)"""
    if not app_state.selected_id:
        return jsonify({"status": "error", "message": "User ID is not selected"})
        
    data = request.json
    image_name = data.get('image_name')
    
    if not image_name:
        return jsonify({"status": "error", "message": "Image name is missing"})
    
    try:
        # 라벨 디렉토리 경로
        label_dir = get_labels_path(app_state.selected_id)
        label_dir.mkdir(parents=True, exist_ok=True)
        
        # 라벨 파일 이름 (확장자 변경)
        label_name = pathlib.Path(image_name).stem + '.txt'
        label_path = label_dir / label_name
        
        # 기존 파일이 있는지 확인하고 삭제
        if label_path.exists():
            label_path.unlink()  # 파일 삭제
            
        # 빈 파일 생성
        with open(label_path, 'w') as f:
            pass  # 내용 없이 빈 파일 생성
            
        # 메모리에서 해당 이미지의 바운딩 박스 초기화
        if image_name in app_state.bboxes:
            app_state.bboxes[image_name] = []
        
        return jsonify({"status": "success", "message": "No fracture label created"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def get_labeling_progress(user_id):
    """사용자 ID에 대한 라벨링 진행 상황 계산"""
    # 전체 이미지 목록
    image_files = get_image_files()  # WebP 파일만 가져오기
    total_images = len(image_files)
    
    if total_images == 0:
        return 0, 0, 0  # 이미지가 없는 경우
    
    # 라벨이 있는 이미지 수 계산
    labels_path = get_labels_path(user_id)
    labeled_count = 0
    
    for img_name in image_files:
        label_name = pathlib.Path(img_name).stem + '.txt'
        label_path = labels_path / label_name
        
        # 라벨 파일이 존재하면 카운트 (내용이 비어있어도 카운트)
        if label_path.exists():
            labeled_count += 1
    
    # 진행률 계산
    progress_percent = (labeled_count / total_images) * 100
    
    return labeled_count, total_images, progress_percent

@app.route('/debug')
def debug_info():
    """디버깅 정보 제공"""
    image_files = get_image_files()
    if not image_files:
        return "이미지 파일이 없습니다."
    
    current_image = image_files[0]
    image_path = f"images/{current_image}"
    static_path = url_for('static', filename=image_path)
    abs_path = pathlib.Path(app.static_folder) / 'images' / current_image
    
    debug = {
        "current_image": current_image,
        "image_url": static_path,
        "abs_path": str(abs_path),
        "abs_path_exists": abs_path.exists(),
        "all_images": image_files
    }
    
    return jsonify(debug)

if __name__ == '__main__':
    # 기본 폴더 생성
    static_images_path.mkdir(parents=True, exist_ok=True)
    
    # ID별 폴더 생성
    for id in range(1, 8):  # ID 1~7 (7 추가)
        id_labels_path = get_labels_path(id)
        id_labels_path.mkdir(parents=True, exist_ok=True)
    
    # static/images 디렉토리 생성
    static_images_dir = pathlib.Path(app.static_folder) / 'images'
    static_images_dir.mkdir(parents=True, exist_ok=True)
    
    # 이미지 변환 및 복사 스크립트 실행
    from convert_and_copy_images import setup_image_serving
    setup_image_serving()
    
    app.run(debug=True, host='0.0.0.0', port=5000)