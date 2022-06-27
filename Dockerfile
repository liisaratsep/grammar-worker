ARG MODEL_IMAGE="model-cp"

FROM python:3.10 as env

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    g++ \
    libffi-dev \
    musl-dev \
    git \
    git-lfs && \
    git lfs install

ENV PYTHONIOENCODING=utf-8
ENV MKL_NUM_THREADS=""

WORKDIR /app

RUN adduser --system --group app && chown -R app:app /app
USER app

ENV PATH="/home/app/.local/bin:${PATH}"

COPY --chown=app:app requirements.txt .
RUN pip install --user -r requirements.txt && \
    rm requirements.txt && \
    python -c "import nltk; nltk.download(\"punkt\")"

ENTRYPOINT ["python", "main.py"]

FROM busybox as model-cp

ARG MODEL_DIR=./models

COPY ${MODEL_DIR} /models

FROM $MODEL_IMAGE as model

FROM env as worker-model

COPY --chown=app:app --from=model /models /app/models
COPY --chown=app:app . .

FROM env as worker-base

COPY --chown=app:app . .