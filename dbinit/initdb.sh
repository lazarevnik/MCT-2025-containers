if [ ! -z "$(ls -A $PGDATA 2>/dev/null)" ]; then
	echo initdb.sh: postgres data directory already initialized, exiting.
	exit 0
fi

apk add postgresql
mkdir /run/postgresql
chown postgres:postgres /run/postgresql
su -c "
pg_ctl init -o \"-c listen_addresses='*'\"
pg_ctl start
psql <<-EOSQL
	CREATE USER \"11cloud2\" PASSWORD '$POSTGRES_PASSWORD';
	CREATE DATABASE \"11cloud2_db\" OWNER \"11cloud2\";
	GRANT ALL PRIVILEGES ON DATABASE \"11cloud2_db\" TO \"11cloud2\";
EOSQL
psql -U $POSTGRES_USER -d $POSTGRES_DB <<-EOSQL
	CREATE TABLE IF NOT EXISTS visits (
		id SERIAL PRIMARY KEY,
		data text
	);
EOSQL
pg_ctl stop" postgres