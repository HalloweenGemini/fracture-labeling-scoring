# Python 3.9를 기반으로 하는 공식 이미지 사용
FROM python:3.9-slim

# 작업 디렉터리 설정
WORKDIR /app

# OpenCV 의존성 설치
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 필요한 패키지 목록 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 폴더가 없는 경우를 대비한 기본 구조 생성 (이미 있으면 무시됨)
RUN mkdir -p /app/Pilot_wrist_0615/Test/images
RUN mkdir -p /app/Pilot_wrist_0615/Test/id1/labels
RUN mkdir -p /app/Pilot_wrist_0615/Test/id2/labels
RUN mkdir -p /app/Pilot_wrist_0615/Test/id3/labels
RUN mkdir -p /app/Pilot_wrist_0615/Test/id4/labels
RUN mkdir -p /app/Pilot_wrist_0615/Test/id5/labels
RUN mkdir -p /app/Pilot_wrist_0615/Test/id6/labels
RUN mkdir -p /app/Pilot_wrist_0615/Test/id7/labels

# Pilot_wrist_0615/Test 디렉토리 전체를 이미지에 복사
COPY Pilot_wrist_0615/Test/ /app/Pilot_wrist_0615/Test/

# 웹앱 실행을 위한 포트 공개
EXPOSE 5000

# 컨테이너 시작 시 실행할 명령어 (Gunicorn으로 변경)
# 워커 수를 2로 설정 (2코어 PC에서 안정적으로 실행하기 위함)
CMD ["gunicorn", "--workers=1", "--bind=0.0.0.0:5000", "app:app"]
