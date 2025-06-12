FROM golang:1.20-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY main.go .

RUN go build -o worker .

FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/worker .

EXPOSE 8000

CMD ["./worker"]
