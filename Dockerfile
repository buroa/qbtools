FROM rust:latest as builder
ENV DEBIAN_FRONTEND noninteractive
WORKDIR /usr/src/myapp
RUN apt update && apt install -y clang upx binutils --no-install-recommends && rm -rf /var/lib/apt/lists/*
RUN cargo install --version 0.13.0 pyoxidizer
COPY . .
RUN pyoxidizer build --release
RUN strip build/x86_64-unknown-linux-gnu/release/install/qbittools
RUN upx --best --lzma build/x86_64-unknown-linux-gnu/release/install/qbittools

FROM debian:buster-slim
ENV DEBIAN_FRONTEND noninteractive
RUN apt update && apt install -y git ca-certificates --no-install-recommends && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/src/myapp/build/x86_64-unknown-linux-gnu/release/install/qbittools /qbittools
CMD ["/qbittools"]
