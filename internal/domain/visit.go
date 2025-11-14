package domain

import (
	"context"
	"time"
)

type Visit struct {
	ID        int64     `json:"id"`
	IP        string    `json:"ip"`
	Count     int64     `json:"count"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type VisitStats struct {
	IP    string `json:"ip"`
	Count int64  `json:"count"`
}

type VisitRepository interface {
	// if the IP doesn't exist, creates a new record with count = 1
	IncrementVisit(ctx context.Context, ip string) error

	GetVisitCount(ctx context.Context, ip string) (int64, error)

	GetAllVisits(ctx context.Context) ([]Visit, error)

	Close() error
}

type CacheRepository interface {
	Get(ctx context.Context, key string) (string, error)

	Set(ctx context.Context, key string, value string, expiration time.Duration) error

	Delete(ctx context.Context, key string) error

	Increment(ctx context.Context, key string) (int64, error)

	Close() error
}
