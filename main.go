package main

import (
	"context"
	"errors"
	"fmt"
	"github.com/redis/go-redis/v9"
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

	conn, err := pgxpool.New(ctx, connStr)
	defer conn.Close()
	if err != nil {
		log.Error("connect to db", "err", err)
	}

	err = conn.Ping(ctx)
	if err != nil {
		log.Error("ping db", "err", err)
	}

	redisHost := os.Getenv("REDIS_HOST")
	redisPort := os.Getenv("REDIS_PORT")
	redisPassword := os.Getenv("REDIS_PASSWORD")
	redisAddr := fmt.Sprintf("%s:%s", redisHost, redisPort)

	redisCache := redis.NewClient(&redis.Options{
		Addr:     redisAddr,
		Password: redisPassword,
	})

	var baseCount int64
	err = conn.QueryRow(ctx, "SELECT count FROM visits_counter").Scan(&baseCount)
	if err != nil {
		log.Error("select visits counter", "err", err)
		return
	}

	_, err = redisCache.Set(ctx, "visits_counter", strconv.FormatInt(baseCount, 10), redis.KeepTTL).Result()
	if err != nil {
		log.Error("redis base count", "err", err)
		return
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

		_, err = redisCache.Incr(ctx, "visits_counter").Result()
		if err != nil {
			log.Error("redis increment", "err", err)
			c.String(http.StatusInternalServerError, "redis increment error")
			return
		}

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

	router.GET("/visits_cache", func(c *gin.Context) {
		redisCount, err := redisCache.Get(ctx, "visits_counter").Result()
		if errors.Is(err, redis.Nil) {
			redisCount = "0"
		} else if err != nil {
			log.Error("redis get visits counter", "err", err)
			c.String(http.StatusInternalServerError, "redis get visits counter error")
			return
		}
		c.String(http.StatusOK, redisCount)
	})

	err = router.Run(":5000")
	if err != nil {
		log.Error("failed to run server", "err", err)
	}
}
