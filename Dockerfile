FROM python:alpine
RUN adduser -D augustin -h /opt/cauch-e
WORKDIR /opt/cauch-e
USER augustin
RUN python -m pip install poetry
COPY pyproject.toml README.md ./
COPY cauch_e/ ./cauch_e/
RUN python -m poetry install
ENTRYPOINT ["python", "-m", "poetry", "run", "python", "-m", "cauch_e"]
