FROM rust:latest as builder
WORKDIR /usr/src/myapp
COPY . .
RUN apt-get update && apt-get install -y clang && rm -rf /var/lib/apt/lists/*
RUN cargo install pyoxidizer
RUN pyoxidizer build --release

FROM debian:buster-slim
COPY --from=builder /usr/src/myapp/build/x86_64-unknown-linux-gnu/release/install/qbittools /qbittools
CMD ["/qbittools"]
