FROM python:3.12-alpine

RUN addgroup -g 10001 relay \
 && adduser \
      -D \
      -H \
      -u 10001 \
      -G relay \
      relay

WORKDIR /app

COPY --chown=10001:10001 relay.py /app/relay.py

RUN chmod 0555 /app/relay.py

USER 10001:10001

ENTRYPOINT ["python3", "/app/relay.py"]
