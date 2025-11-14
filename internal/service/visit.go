package service

import (
	"context"
	"errors"
	"fmt"
	"strconv"
	"time"

	"d4y2k.me/go-simple-api/internal/domain"
)

const (
	visitCountCachePrefix = "visit:count:"
	cacheTTL              = 5 * time.Minute
)

type VisitService struct {
	visitRepo domain.VisitRepository
	cache     domain.CacheRepository
}

func NewVisitService(visitRepo domain.VisitRepository, cache domain.CacheRepository) *VisitService {
	return &VisitService{
		visitRepo: visitRepo,
		cache:     cache,
	}
}

func (s *VisitService) RecordPing(ctx context.Context, ip string) error {
	if ip == "" {
		return domain.ErrInvalidInput
	}

	if err := s.visitRepo.IncrementVisit(ctx, ip); err != nil {
		return fmt.Errorf("failed to record visit: %w", err)
	}

	cacheKey := visitCountCachePrefix + ip
	_ = s.cache.Delete(ctx, cacheKey)

	return nil
}

func (s *VisitService) GetVisitCount(ctx context.Context, ip string) (int64, error) {
	if ip == "" {
		return 0, domain.ErrInvalidInput
	}

	cacheKey := visitCountCachePrefix + ip
	if cachedCount, err := s.cache.Get(ctx, cacheKey); err == nil {
		count, err := strconv.ParseInt(cachedCount, 10, 64)
		if err == nil {
			return count, nil
		}
	}

	count, err := s.visitRepo.GetVisitCount(ctx, ip)
	if err != nil {
		if errors.Is(err, domain.ErrNotFound) {
			return 0, nil
		}
		return 0, fmt.Errorf("failed to get visit count: %w", err)
	}

	_ = s.cache.Set(ctx, cacheKey, strconv.FormatInt(count, 10), cacheTTL)

	return count, nil
}

func (s *VisitService) GetAllVisits(ctx context.Context) ([]domain.Visit, error) {
	visits, err := s.visitRepo.GetAllVisits(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get all visits: %w", err)
	}
	return visits, nil
}
