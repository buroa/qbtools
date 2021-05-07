FROM python:3 as builder
ENV DEBIAN_FRONTEND noninteractive
RUN apt update && apt install -y clang upx binutils musl-tools --no-install-recommends && rm -rf /var/lib/apt/lists/*
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN rustup target add x86_64-unknown-linux-musl
RUN python3 -m pip install pyoxidizer==0.15.0
WORKDIR /usr/src/myapp
COPY . .
RUN pyoxidizer build --release --target-triple x86_64-unknown-linux-musl
RUN strip build/x86_64-unknown-linux-musl/release/install/qbittools
RUN upx --best --lzma build/x86_64-unknown-linux-musl/release/install/qbittools

FROM alpine:latest
RUN apk add --no-cache git ca-certificates
COPY --from=builder /usr/src/myapp/build/x86_64-unknown-linux-musl/release/install/qbittools /usr/local/bin/qbittools
ENTRYPOINT ["qbittools"]
