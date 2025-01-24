FROM python:3.9

WORKDIR /app

# 가상환경 설정
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 의존성 설치 (캐시 활용을 위해 requirements.txt만 먼저 복사)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 정적 파일 디렉토리 생성
RUN mkdir -p /app/staticfiles /app/media

# 프로젝트 파일 복사
COPY . .

# collectstatic은 docker-compose의 command에서 실행하도록 변경