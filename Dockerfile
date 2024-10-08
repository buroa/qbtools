FROM docker.io/library/python:3.13-alpine AS base

FROM base AS pip
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir --prefix=/install --requirement /requirements.txt \
    && python -c "import compileall; compileall.compile_path(maxlevels=10)"

FROM base AS app
WORKDIR /app
COPY qbtools/ .
RUN python -m compileall qbtools.py commands/

FROM base AS final
WORKDIR /app
COPY --from=pip /install /usr/local
COPY --from=app /app .
COPY config.yaml /config/config.yaml
ENTRYPOINT ["python3", "qbtools.py"]
