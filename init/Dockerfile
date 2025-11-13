FROM postgres:15-alpine
RUN apk add --no-cache bash
WORKDIR /scripts
COPY init-db.sh .
RUN chmod +x init-db.sh
ENTRYPOINT ["/scripts/init-db.sh"]