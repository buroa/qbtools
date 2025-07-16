# Build stage
FROM golang:1.24-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags="-w -s" -trimpath -o qbtools .

# Runtime stage
FROM scratch

COPY --from=builder /app/qbtools /qbtools
COPY config.yaml /config/config.yaml

ENTRYPOINT ["/qbtools"]
