FROM python:3.9

WORKDIR /app

# 환경 변수 설정
ENV DJANGO_SECRET_KEY=django-insecure-00_8&5m4x*)+o)n_q_dfs3b_8hl1)r$5*0ngxejb^=i*pwfh33
ENV DJANGO_DEBUG=False
ENV DJANGO_ALLOWED_HOSTS=52.78.197.80,localhost,127.0.0.1
ENV POSTGRES_DB=watson
ENV POSTGRES_USER=anem1c
ENV POSTGRES_PASSWORD=lsh9123
ENV POSTGRES_HOST=52.78.197.80
ENV POSTGRES_PORT=5432

# pip 경고 해결을 위한 가상환경 설정
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput