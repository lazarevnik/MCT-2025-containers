package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"time"

	"github.com/julienschmidt/httprouter"
	"github.com/redis/go-redis/v9"
	"github.com/uptrace/bun"
	"github.com/uptrace/bun/dialect/pgdialect"
	"github.com/uptrace/bun/driver/pgdriver"
)

var (
	db    *bun.DB
	cache *redis.Client
	ctx   = context.Background()
)

type Visit struct {
	bun.BaseModel `bun:"table:visits"`

	IPAddress string    `bun:"address,type:varchar"`
	VisitTime time.Time `bun:"visit_date,type:timestamp"`
}

func initDB() {
	var (
		err error
	)
	dsn := fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=disable",
		os.Getenv("DB_USER"),
		os.Getenv("DB_PASSWORD"),
		os.Getenv("DB_HOST"),
		os.Getenv("DB_PORT"),
		os.Getenv("DB_NAME"),
	)

	db = bun.NewDB(
		sql.OpenDB(
			pgdriver.NewConnector(pgdriver.WithDSN(dsn)),
		),
		pgdialect.New(),
	)

	if err = db.Ping(); err != nil {
		log.Fatal("Could not connect to database:", err)
	}
}

func InitCache() {
	var (
		err error
	)
	redisHost := os.Getenv("REDIS_HOST")
	redisPort := os.Getenv("REDIS_PORT")

	cache = redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%s", redisHost, redisPort),
		Password: "",
		DB:       0,
	})

	err = cache.Ping(ctx).Err()
	if err != nil {
		log.Fatal("Could not start cache")
		return
	}
	UpdateCache()

}

func UpdateCache() {
	var (
		count int
		err   error
	)
	err = db.NewSelect().ColumnExpr("COUNT(*)").Model((*Visit)(nil)).Scan(ctx, &count)
	if err != nil {
		log.Printf("Error getting cache: %v", err)
		return
	}

	err = cache.Set(ctx, "visits_count", count, 0).Err()
	if err != nil {
		log.Printf("Error setting cache: %v", err)
		return
	}
}

func PingServ(w http.ResponseWriter, r *http.Request, _ httprouter.Params) {
	var (
		err error
	)
	clientIP := r.RemoteAddr
	if host, _, err := net.SplitHostPort(clientIP); err == nil {
		clientIP = host
	}
	visit := &Visit{
		IPAddress: clientIP,
		VisitTime: time.Now(),
	}
	_, err = db.NewInsert().Model(visit).Exec(ctx)
	if err != nil {
		http.Error(w, "Internal error", http.StatusInternalServerError)
		log.Printf("Error inserting visit: %v", err)
		return
	}
	err = cache.Incr(ctx, "visits_count").Err()
	if err != nil {
		http.Error(w, "Internal error", http.StatusInternalServerError)
		log.Printf("Error updating cache: %v", err)
		return
	}

	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("pong"))
}

func VisitServ(w http.ResponseWriter, r *http.Request, _ httprouter.Params) {
	var (
		err   error
		count int
	)
	val, err := cache.Get(ctx, "visits_count").Result()
	if err == nil {
		w.Header().Set("Content-Type", "text/plain")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(val))
		return
	}

	err = db.NewSelect().ColumnExpr("COUNT(*)").Model((*Visit)(nil)).Scan(ctx, &count)
	if err != nil {
		http.Error(w, "Internal error", http.StatusInternalServerError)
		log.Printf("Error getting counter: %v", err)
		return
	}

	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(fmt.Sprintf("%d", count)))
}

func ClearCacheServ(w http.ResponseWriter, r *http.Request, _ httprouter.Params) {
	var (
		err error
	)
	err = cache.Del(ctx, "visits_count").Err()
	if err != nil {
		http.Error(w, "Error clearing cache", http.StatusInternalServerError)
		return
	}

	UpdateCache()
	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("Cache updated"))
}

func main() {
	initDB()
	InitCache()
	defer db.Close()
	defer cache.Close()

	router := httprouter.New()

	router.GET("/", func(w http.ResponseWriter, r *http.Request, _ httprouter.Params) {
		w.Header().Set("Content-Type", "text/plain")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	router.GET("/ping", PingServ)
	router.GET("/visits", VisitServ)
	router.GET("/visits/clear-cache", ClearCacheServ)

	port := os.Getenv("APP_PORT")
	if port == "" {
		port = "8080"
	}

	log.Fatal(http.ListenAndServe(":"+port, router))
}
