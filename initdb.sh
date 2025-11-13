apk add postgresql
mkdir /run/postgresql
chown postgres:postgres /run/postgresql
su -c "
rm -rf $PGDATA/*
pg_ctl init
pg_ctl start
psql <<-EOSQL
	CREATE USER \"11cloud2\" PASSWORD '$POSTGRES_PASSWORD';
	CREATE DATABASE \"11cloud2_db\" OWNER \"11cloud2\";
	GRANT ALL PRIVILEGES ON DATABASE \"11cloud2_db\" TO \"11cloud2\";
EOSQL
psql -U $POSTGRES_USER -d $POSTGRES_DB <<-EOSQL
	CREATE TABLE IF NOT EXISTS visits (
		id integer PRIMARY KEY,
		data text
	);
EOSQL
pg_ctl stop" postgres