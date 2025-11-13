package app

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"strings"

	"github.com/redis/go-redis/v9"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

var (
	db  *gorm.DB
	rdb *redis.Client
	ctx = context.Background()
)

type Visit struct {
	ID        uint   `gorm:"primaryKey"`
	IP        string `gorm:"index"`
	CreatedAt int64  `gorm:"autoCreateTime:milli"`
}

func init() {
	var err error

	dsn := fmt.Sprintf("user=%s password=%s host=%s port=%s dbname=%s sslmode=disable",
		os.Getenv("DB_USER"),
		os.Getenv("DB_PASSWORD"),
		os.Getenv("DB_HOST"),
		os.Getenv("DB_PORT"),
		os.Getenv("DB_NAME"),
	)

	db, err = gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		panic(fmt.Sprintf("failed to connect to database: %v", err))
	}

	rdb = redis.NewClient(&redis.Options{
		Addr: os.Getenv("REDIS_ADDR"),
	})

	if err := rdb.Ping(ctx).Err(); err != nil {
		panic(fmt.Sprintf("failed to connect to redis: %v", err))
	}
}

func handlePing(w http.ResponseWriter, r *http.Request) {
	devMode := os.Getenv("DEV_MODE") == "true"

	ip := getClientIP(r)

	if !devMode {
		visit := Visit{IP: ip}
		if err := db.Create(&visit).Error; err != nil {
			http.Error(w, "Database error", http.StatusInternalServerError)
			return
		}

		rdb.Del(ctx, "visits_count")
	}

	w.Header().Set("Content-Type", "text/plain")
	_, err := fmt.Fprint(w, "pong")
	if err != nil {
		return
	}
}

func handleVisits(w http.ResponseWriter, r *http.Request) {
	devMode := os.Getenv("ENV") != "prod"

	if devMode {
		w.Header().Set("Content-Type", "text/plain")
		_, err := fmt.Fprint(w, -1)
		if err != nil {
			return
		}
		return
	}

	// Try to get from cache first
	val, err := rdb.Get(ctx, "visits_count").Result()
	if err == nil {
		w.Header().Set("Content-Type", "text/plain")
		_, err := fmt.Fprint(w, val)
		if err != nil {
			return
		}
		return
	}

	// Query from database
	var count int64
	if err := db.Model(&Visit{}).Count(&count).Error; err != nil {
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Cache the result
	rdb.Set(ctx, "visits_count", count, 0)

	w.Header().Set("Content-Type", "text/plain")
	_, err = fmt.Fprint(w, count)
	if err != nil {
		return
	}
}

func getClientIP(r *http.Request) string {
	if forwardedHeader := r.Header.Get("X-Forwarded-For"); forwardedHeader != "" {
		ips := strings.Split(forwardedHeader, ",")
		return strings.TrimSpace(ips[0])
	}
	if realHeader := r.Header.Get("X-Real-IP"); realHeader != "" {
		return realHeader
	}
	return strings.Split(r.RemoteAddr, ":")[0]
}

func main() {
	http.HandleFunc("/ping", handlePing)
	http.HandleFunc("/visits", handleVisits)
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain")
		_, err := fmt.Fprint(w, "ok")
		if err != nil {
			return
		}
	})

	fmt.Println("Server starting on :8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		panic(err)
	}
}
