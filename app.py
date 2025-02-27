from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import glob
import json
import time
from datetime import datetime
import cv2

app = Flask(__name__)

# 세션 데이터를 저장할 전역 변수
class AppState:
    def __init__(self):
        self.start_time = time.time()
        self.current_image_idx = 0
        self.bboxes = {}  # 이미지별 바운딩 박스 저장
        self.selected_id = None

app_state = AppState()

# 폴더 경로 설정
base_path = "Pilot_wrist_0615/Test"
images_path = os.path.join(base_path, "images")

def get_labels_path(user_id):
    """사용자 ID에 따른 labels 경로 반환"""
    return os.path.join(base_path, f"id{user_id}", "labels")

def load_bboxes_for_image(image_name, user_id):
    """특정 이미지와 사용자 ID에 대한 바운딩 박스 로드"""
    labels_path = get_labels_path(user_id)
    label_name = os.path.splitext(image_name)[0] + '.txt'
    label_path = os.path.join(labels_path, label_name)
    
    bboxes = []
    
    if os.path.exists(label_path):
        img_path = os.path.join(images_path, image_name)
        img = cv2.imread(img_path)
        img_height, img_width = img.shape[:2]
        
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
    
    return bboxes

@app.route('/')
def index():
    # ID 선택 페이지
    return render_template('index.html')

@app.route('/select_id/<int:id>')
def select_id(id):
    app_state.selected_id = id
    app_state.start_time = time.time()
    app_state.bboxes = {}  # ID가 변경되면 바운딩 박스 초기화
    
    # ID별 labels 폴더 생성
    labels_path = get_labels_path(id)
    os.makedirs(labels_path, exist_ok=True)
    
    # 현재 이미지의 바운딩 박스 로드
    image_files = sorted(glob.glob(os.path.join(images_path, "*.png")))
    image_names = [os.path.basename(img) for img in image_files]
    
    # 현재 ID의 모든 이미지에 대한 바운딩 박스 미리 로드
    for image_name in image_names:
        app_state.bboxes[image_name] = load_bboxes_for_image(image_name, id)
    
    return redirect(url_for('main_app'))

@app.route('/main')
def main_app():
    # 이미지 파일 목록 가져오기
    image_files = sorted(glob.glob(os.path.join(images_path, "*.png")))
    image_names = [os.path.basename(img) for img in image_files]
    
    # 현재 선택된 이미지
    current_image = image_names[app_state.current_image_idx]
    
    # 이미지 경로 (상대 경로)
    image_path = f"images/{current_image}"
    
    # 현재 이미지에 저장된 바운딩 박스
    # 메모리에 없으면 파일에서 로드
    if current_image not in app_state.bboxes:
        app_state.bboxes[current_image] = load_bboxes_for_image(current_image, app_state.selected_id)
    
    current_bboxes = app_state.bboxes.get(current_image, [])
    
    # 경과 시간 계산
    elapsed_time = int(time.time() - app_state.start_time)
    minutes = elapsed_time // 60
    seconds = elapsed_time % 60
    timer = f"{minutes:02d}:{seconds:02d}"
    
    return render_template(
        'main.html', 
        user_id=app_state.selected_id,
        image_path=image_path,
        image_name=current_image,
        image_list=image_names,
        current_idx=app_state.current_image_idx,
        bboxes=json.dumps(current_bboxes),
        timer=timer
    )

@app.route('/next_image')
def next_image():
    image_files = sorted(glob.glob(os.path.join(images_path, "*.png")))
    if app_state.current_image_idx < len(image_files) - 1:
        app_state.current_image_idx += 1
    return redirect(url_for('main_app'))

@app.route('/prev_image')
def prev_image():
    if app_state.current_image_idx > 0:
        app_state.current_image_idx -= 1
    return redirect(url_for('main_app'))

@app.route('/select_image/<int:idx>')
def select_image(idx):
    image_files = sorted(glob.glob(os.path.join(images_path, "*.png")))
    if 0 <= idx < len(image_files):
        app_state.current_image_idx = idx
    return redirect(url_for('main_app'))

@app.route('/save_bbox', methods=['POST'])
def save_bbox():
    data = request.json
    image_name = data.get('image_name')
    bbox = data.get('bbox')  # [x, y, width, height, class_id]
    
    if image_name not in app_state.bboxes:
        app_state.bboxes[image_name] = []
    
    app_state.bboxes[image_name].append(bbox)
    
    # YOLO 형식으로 라벨 저장
    save_yolo_label(image_name, bbox)
    
    return jsonify({'status': 'success'})

def save_yolo_label(image_name, bbox):
    # 실제 이미지 크기 가져오기
    img_path = os.path.join(images_path, image_name)
    img = cv2.imread(img_path)
    img_height, img_width = img.shape[:2]
    
    x, y, width, height, class_id = bbox
    
    # YOLO 형식으로 변환
    x_center = (x + width/2) / img_width
    y_center = (y + height/2) / img_height
    norm_width = width / img_width
    norm_height = height / img_height
    
    # ID별 labels 폴더에 저장
    labels_path = get_labels_path(app_state.selected_id)
    label_name = os.path.splitext(image_name)[0] + '.txt'
    label_path = os.path.join(labels_path, label_name)
    
    new_line = f"{class_id} {x_center:.6f} {y_center:.6f} {norm_width:.6f} {norm_height:.6f}\n"
    
    # 기존 라벨이 있으면 추가, 없으면 새로 생성
    with open(label_path, 'a') as f:
        f.write(new_line)

@app.route('/get_timer')
def get_timer():
    elapsed_time = int(time.time() - app_state.start_time)
    minutes = elapsed_time // 60
    seconds = elapsed_time % 60
    timer = f"{minutes:02d}:{seconds:02d}"
    return jsonify({'timer': timer})

@app.route('/delete_last_bbox', methods=['POST'])
def delete_last_bbox():
    data = request.json
    image_name = data.get('image_name')
    
    # 메모리에서 삭제
    if image_name in app_state.bboxes and app_state.bboxes[image_name]:
        app_state.bboxes[image_name].pop()
    
    # 파일에서 삭제
    labels_path = get_labels_path(app_state.selected_id)
    label_name = os.path.splitext(image_name)[0] + '.txt'
    label_path = os.path.join(labels_path, label_name)
    
    if os.path.exists(label_path):
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
    label_name = os.path.splitext(image_name)[0] + '.txt'
    label_path = os.path.join(labels_path, label_name)
    
    if os.path.exists(label_path):
        try:
            # 파일 비우기
            with open(label_path, 'w') as f:
                pass
        except Exception as e:
            print(f"파일 처리 오류: {e}")
            return jsonify({'status': 'error', 'message': str(e)})
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    # 기본 폴더 생성
    os.makedirs(images_path, exist_ok=True)
    
    # ID별 폴더 생성
    for id in range(1, 7):  # ID 1~6
        id_labels_path = get_labels_path(id)
        os.makedirs(id_labels_path, exist_ok=True)
    
    # 정적 파일을 위한 심볼릭 링크 생성
    static_images_dir = os.path.join(app.static_folder, 'images')
    if not os.path.exists(static_images_dir):
        os.makedirs(static_images_dir, exist_ok=True)
    
    # 실제 이미지 폴더와 static 폴더 연결
    for img_file in glob.glob(os.path.join(images_path, "*.png")):
        img_name = os.path.basename(img_file)
        target_path = os.path.join(static_images_dir, img_name)
        if not os.path.exists(target_path):
            try:
                os.symlink(img_file, target_path)
            except:
                import shutil
                shutil.copy2(img_file, target_path)
    
    app.run(debug=True) 