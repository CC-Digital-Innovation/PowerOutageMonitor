FROM golang:1.14 as builder
ADD . $GOPATH/src/github.com/opsgenie/oec
WORKDIR $GOPATH/src/github.com/opsgenie/oec/main
RUN export GIT_COMMIT=$(git rev-list -1 HEAD) && \
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -a -installsuffix cgo \
        -ldflags "-X main.OECCommitVersion=$GIT_COMMIT -X main.OECVersion=1.0.1" -o nocgo -o /oec .
FROM python:alpine3.12 as base
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN addgroup -S --gid 1001 jle && \
    adduser -S --uid 1001 jle -G jle && \
    apk update && \
    apk add --no-cache git ca-certificates && \
    update-ca-certificates
COPY --from=builder /oec /opt/oec
RUN mkdir -p /var/log/opsgenie && \
    chown -R jle:jle /var/log/opsgenie && \
    chown -R jle:jle /opt/oec
USER jle
ENTRYPOINT ["/opt/oec"]
