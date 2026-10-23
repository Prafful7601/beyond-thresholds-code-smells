# CodeSniff API. Build from the REPOSITORY ROOT (the image needs src/ and results/ from the paper):
#   docker build -f webapp/backend/Dockerfile -t codesniff-api .
#   docker run -p 8000:8000 -e GITHUB_TOKEN=... codesniff-api
# No DACOS raw data is copied: the models are pre-trained (webapp/backend/models) and the findings come from
# results/paper_numbers.json and results/tables/*.csv.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    CODESNIFF_ROOT=/srv/paper CODESNIFF_DB=/data/codesniff.db PORT=8000
WORKDIR /srv/paper/webapp/backend

COPY webapp/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Feature definitions (src/features.py imports src/common.py) and the paper's result tables.
COPY src/features.py src/common.py /srv/paper/src/
COPY results/paper_numbers.json /srv/paper/results/paper_numbers.json
COPY results/tables /srv/paper/results/tables
COPY webapp/backend/main.py webapp/backend/cli.py ./
COPY webapp/backend/codesniff ./codesniff
COPY webapp/backend/models ./models

RUN mkdir -p /data && useradd --create-home codesniff && chown codesniff /data
USER codesniff
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health')"
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
