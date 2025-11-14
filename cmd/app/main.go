package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/lazarevnik/MCT-2025-containers/config"
	httpDelivery "github.com/lazarevnik/MCT-2025-containers/internal/delivery/http"
	"github.com/lazarevnik/MCT-2025-containers/internal/domain"
	"github.com/lazarevnik/MCT-2025-containers/internal/repository/postgres"
	redisRepo "github.com/lazarevnik/MCT-2025-containers/internal/repository/redis"
	"github.com/lazarevnik/MCT-2025-containers/internal/usecase"
	pgClient "github.com/lazarevnik/MCT-2025-containers/pkg/postgres"
	redisClient "github.com/lazarevnik/MCT-2025-containers/pkg/redis"
)

type dummyRepository struct{}

func (d *dummyRepository) Create(ipAddress string) error { return nil }
func (d *dummyRepository) Count() (int64, error)         { return 0, nil }

type dummyCache struct{}

func (d *dummyCache) Get(ctx context.Context) (int64, error)     { return 0, nil }
func (d *dummyCache) Set(ctx context.Context, count int64) error { return nil }
func (d *dummyCache) Invalidate(ctx context.Context) error       { return nil }
func (d *dummyCache) Increment(ctx context.Context) error        { return nil }

func main() {
	cfg := config.Load()

	var visitUC domain.VisitUseCase

	if cfg.DevMode {
		visitRepo := &dummyRepository{}
		visitCache := &dummyCache{}
		visitUC = usecase.NewVisitUseCase(visitRepo, visitCache)
	} else {
		var db *pgClient.DB
		var err error
		maxRetries := 3
		for i := 0; i < maxRetries; i++ {
			db, err = pgClient.NewPostgresDB(cfg.Database)
			if err == nil {
				log.Println("Successfully connected to database")
				break
			}
			log.Printf("Failed to connect to database (attempt %d/%d): %v", i+1, maxRetries, err)
			time.Sleep(time.Second * 2)
		}

		if err != nil {
			log.Fatalf("Could not connect to database after %d attempts: %v", maxRetries, err)
		}
		defer db.Close()

		var redis *redisClient.Client
		for i := 0; i < maxRetries; i++ {
			redis, err = redisClient.NewRedisClient(cfg.Redis.Addr, cfg.Redis.Password, cfg.Redis.DB)
			if err == nil {
				log.Println("Successfully connected to Redis")
				break
			}
			log.Printf("Failed to connect to Redis (attempt %d/%d): %v", i+1, maxRetries, err)
			time.Sleep(time.Second * 2)
		}

		if err != nil {
			log.Fatalf("Could not connect to Redis after %d attempts: %v", maxRetries, err)
		}
		defer redis.Close()

		visitRepo := postgres.NewVisitRepository(db)
		visitCache := redisRepo.NewVisitCache(redis)

		visitUC = usecase.NewVisitUseCase(visitRepo, visitCache)
	}

	router := httpDelivery.SetupRouter(visitUC, cfg.DevMode)

	addr := fmt.Sprintf(":%s", cfg.Server.Port)
	log.Printf("Starting server on %s", addr)
	if err := router.Run(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
