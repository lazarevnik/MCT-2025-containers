FROM postgres:13

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY init.sql /scripts/init.sql
COPY init.sh /scripts/init.sh

RUN chmod +x /scripts/init.sh

WORKDIR /scripts

CMD ["/scripts/init.sh"]
