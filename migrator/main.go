package main

import (
	"context"
	"fmt"
	"log/slog"
	"os"

	"github.com/jackc/pgx/v5/pgxpool"
)

const queryIPs = "CREATE TABLE IF NOT EXISTS client_ips (id SERIAL PRIMARY KEY, ip_address TEXT NOT NULL, requested_at TIMESTAMPTZ DEFAULT now());"
const (
	queryVisitsCreate = "CREATE TABLE IF NOT EXISTS visits_counter (count BIGINT NOT NULL DEFAULT 0);"
	queryVisitsInsert = "INSERT INTO visits_counter (count) SELECT 0 WHERE NOT EXISTS (SELECT 1 FROM visits_counter);"
)

func main() {
	ctx := context.Background()
	log := slog.Default()

	host := os.Getenv("POSTGRES_HOST")
	db := os.Getenv("POSTGRES_DB")
	user := os.Getenv("POSTGRES_USER")
	password := os.Getenv("POSTGRES_PASSWORD")

	connStr := fmt.Sprintf(
		"postgres://%s:%s@%s/%s?sslmode=disable",
		user, password, host, db,
	)
	conn, err := pgxpool.New(ctx, connStr)
	defer conn.Close()
	if err != nil {
		log.Error("connect to db", "err", err)
	}

	_, err = conn.Exec(ctx, queryIPs)
	if err != nil {
		log.Error("query ips", "err", err)
		return
	}
	_, err = conn.Exec(ctx, queryVisitsCreate)
	if err != nil {
		log.Error("query create ips", "err", err)
		return
	}
	_, err = conn.Exec(ctx, queryVisitsInsert)
	if err != nil {
		log.Error("query insert ips", "err", err)
		return
	}

	return
}
