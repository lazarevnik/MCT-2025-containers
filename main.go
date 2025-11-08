package main

import (
	"context"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"strconv"

	"github.com/gin-gonic/gin"
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

	//conn, err := pgx.Connect(context.Background(), connStr)
	//if err != nil {
	//	log.Error("connect to db", "err", err)
	//}
	conn, err := pgxpool.New(ctx, connStr)
	defer conn.Close()
	if err != nil {
		log.Error("connect to db", "err", err)
	}

	_, err = conn.Query(ctx, queryIPs)
	if err != nil {
		log.Error("query ips", "err", err)
		return
	}
	_, err = conn.Query(ctx, queryVisitsCreate)
	if err != nil {
		log.Error("query create ips", "err", err)
		return
	}
	_, err = conn.Query(ctx, queryVisitsInsert)
	if err != nil {
		log.Error("query insert ips", "err", err)
		return
	}

	err = conn.Ping(ctx)
	if err != nil {
		log.Error("ping db", "err", err)
	}

	router := gin.Default()

	router.GET("/ping", func(c *gin.Context) {
		ip := c.ClientIP()

		_, err = conn.Exec(ctx, "INSERT INTO client_ips (ip_address) VALUES ($1)", ip)
		if err != nil {
			log.Error("insert ip", "err", err)
			c.String(http.StatusInternalServerError, "error saving client ip")
			return
		}

		var count int64
		err = conn.QueryRow(ctx, "UPDATE visits_counter SET count = count + 1 RETURNING count").Scan(&count)
		if err != nil {
			log.Error("update visits counter", "err", err)
			c.String(http.StatusInternalServerError, "update visits counter")
			return
		}
		log.Debug("update visits counter", "count", count)

		c.String(http.StatusOK, "pong")
	})

	router.GET("/visits", func(c *gin.Context) {
		var count int64
		err = conn.QueryRow(ctx, "SELECT count FROM visits_counter").Scan(&count)
		if err != nil {
			log.Error("select visits counter", "err", err)
			c.String(http.StatusInternalServerError, "select visits counter")
			return
		}
		log.Debug("select visits counter", "count", count)
		c.String(http.StatusOK, strconv.FormatInt(count, 10))
	})

	err = router.Run(":5000")
	if err != nil {
		log.Error("failed to run server", "err", err)
	}
}
