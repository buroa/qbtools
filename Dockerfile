FROM python:3.12.3-alpine3.19 as base

FROM base as pip
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r /requirements.txt \
    && python3 -c "import compileall; compileall.compile_path(maxlevels=10)"

FROM base as app
WORKDIR /app
COPY qbtools/ .
RUN python3 -m compileall qbtools.py commands/

FROM base as final
WORKDIR /app
COPY --from=pip /install /usr/local
COPY --from=app /app .
ENTRYPOINT ["python3", "qbtools.py"]
