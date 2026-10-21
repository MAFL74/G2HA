ARG BUILD_FROM=python:3.12-slim
FROM ${BUILD_FROM}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY relay ./relay
RUN pip install .

COPY run.sh /run.sh
RUN chmod a+x /run.sh

EXPOSE 8000
CMD ["/run.sh"]

