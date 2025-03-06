# 손목 X-Ray 골절 라벨링 애플리케이션

이 저장소는 손목 X-Ray 이미지를 라벨링하고 관리하기 위한 웹 애플리케이션을 포함하고 있습니다. Docker를 사용하여 어디서나 쉽게 실행할 수 있습니다.

## 목차
- [소개](#소개)
- [설치 및 실행 방법](#설치-및-실행-방법)
- [볼륨 마운트 설명](#볼륨-마운트-설명)
- [사용 방법](#사용-방법)
- [문제 해결](#문제-해결)

## 소개

이 애플리케이션은 손목 X-Ray 이미지를 라벨링하고 관리하는 웹 인터페이스를 제공합니다. 골절 여부를 표시하거나 경계 상자(bounding box)를 그려 라벨링할 수 있습니다. 진행 상태를 추적하고 관리할 수 있습니다.

## 설치 및 실행 방법

### 필수 조건
- Docker가 설치되어 있어야 합니다. [Docker 설치 방법](https://docs.docker.com/get-docker/)

### Docker Hub에서 이미지 가져오기

```bash
docker pull jaeminlee1996/wrist-scoring:latest
```

### 애플리케이션 실행하기

#### 기본 실행 방법
```bash
docker run -p 5000:5000 jaeminlee1996/wrist-scoring:latest
```

이제 웹 브라우저에서 `http://localhost:5000`으로 접속하면 애플리케이션을 사용할 수 있습니다.

#### 백그라운드에서 실행하기
```bash
docker run -d -p 5000:5000 jaeminlee1996/wrist-scoring:latest
```

## 볼륨 마운트 설명

데이터를 유지하고 라벨링 결과를 저장하려면 볼륨을 마운트해야 합니다. 다음과 같은 방법으로 볼륨을 마운트할 수 있습니다:

### Windows에서 볼륨 마운트

```bash
docker run -p 5000:5000 -v C:\경로\Test:/app/Pilot_wrist_0615/Test jaeminlee1996/wrist-scoring:latest
```

### macOS/Linux에서 볼륨 마운트

```bash
docker run -p 5000:5000 -v /경로/Test:/app/Pilot_wrist_0615/Test jaeminlee1996/wrist-scoring:latest
```

### 현재 디렉토리 기준 상대 경로로 마운트 (PowerShell)

```bash
docker run -p 5000:5000 -v ${PWD}/Test:/app/Pilot_wrist_0615/Test jaeminlee1996/wrist-scoring:latest
```

### 다른 포트 사용하기

만약 5000번 포트가 이미 사용 중이라면, 다른 포트를 사용할 수 있습니다:

```bash
docker run -p 8080:5000 -v C:\경로\Test:/app/Pilot_wrist_0615/Test jaeminlee1996/wrist-scoring:latest
```

이 경우 `http://localhost:8080`으로 접속하면 애플리케이션을 사용할 수 있습니다.

## 사용 방법

1. 웹 브라우저에서 `http://localhost:5000` (또는 지정한 포트)으로 접속합니다.
2. ID를 선택하여 해당 ID의 이미지 목록에 접근합니다.
3. 이미지 목록에서 라벨링할 이미지를 선택합니다.
4. 골절이 없는 경우 "No Fracture" 버튼을 클릭합니다.
5. 골절이 있는 경우 이미지 위에 경계 상자를 그려 라벨링합니다.
6. 라벨링된 이미지는 자동으로 저장되며 진행 상황이 업데이트됩니다.
7. 라벨링된 이미지는 목록에서 체크 표시가 나타납니다.

## 문제 해결

### 볼륨 마운트 오류
Windows에서 볼륨 마운트 시 경로 형식 오류가 발생할 경우, 다음 방법을 시도해 보세요:
```bash
docker run -p 5000:5000 -v //c/Users/경로/Test:/app/Pilot_wrist_0615/Test jaeminlee1996/wrist-scoring:latest
```

### 포트 충돌
5000번 포트가 이미 사용 중인 경우 다른 포트를 사용하세요:
```bash
docker run -p 8080:5000 jaeminlee1996/wrist-scoring:latest
```

### 컨테이너 관리
실행 중인 컨테이너 목록 확인:
```bash
docker ps
```

컨테이너 중지:
```bash
docker stop [컨테이너ID]
```

---

이 README에 대한 피드백이나 추가 질문이 있으시면 GitHub 이슈를 통해 문의해 주세요. 