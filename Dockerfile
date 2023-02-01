FROM python:alpine
RUN adduser -D augustin -h /opt/cauch-e
WORKDIR /opt/cauch-e
USER augustin
RUN python -m pip install poetry
COPY pyproject.toml ./
RUN python -m poetry install --no-root
COPY cauch_e/ ./cauch_e/
ENTRYPOINT ["python", "-m", "poetry", "run", "python", "-m", "cauch_e"]
