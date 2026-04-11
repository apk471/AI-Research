FROM golang:1.25 AS builder

WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/backend ./cmd/go-boilerplate

FROM gcr.io/distroless/base-debian12

WORKDIR /app

COPY --from=builder /out/backend /app/backend
COPY --from=builder /src/static /app/static
COPY --from=builder /src/templates /app/templates

CMD ["/app/backend"]
