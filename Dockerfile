FROM python:3.9

WORKDIR /app

# 가상환경 설정
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 의존성 설치
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# .env 파일이 있을 때만 collectstatic 실행
RUN if [ -f .env ]; then python manage.py collectstatic --noinput; fi