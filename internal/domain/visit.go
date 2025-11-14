package domain

import (
	"context"
	"time"
)

type Visit struct {
	ID        int64     `json:"id"`
	IPAddress string    `json:"ip_address"`
	CreatedAt time.Time `json:"created_at"`
}

type VisitRepository interface {
	Create(ipAddress string) error
	Count() (int64, error)
}

type VisitCache interface {
	Get(ctx context.Context) (int64, error)
	Set(ctx context.Context, count int64) error
	Invalidate(ctx context.Context) error
	Increment(ctx context.Context) error
}

type VisitUseCase interface {
	RecordVisit(ipAddress string) error
	GetVisitsCount() (int64, error)
}
