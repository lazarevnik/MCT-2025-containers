package usecase

import (
	"context"
	"log"

	"github.com/lazarevnik/MCT-2025-containers/internal/domain"
)

type visitUseCase struct {
	visitRepo  domain.VisitRepository
	visitCache domain.VisitCache
}

func NewVisitUseCase(repo domain.VisitRepository, cache domain.VisitCache) domain.VisitUseCase {
	return &visitUseCase{
		visitRepo:  repo,
		visitCache: cache,
	}
}

func (u *visitUseCase) RecordVisit(ipAddress string) error {
	if err := u.visitRepo.Create(ipAddress); err != nil {
		return err
	}

	ctx := context.Background()
	if err := u.visitCache.Increment(ctx); err != nil {
		log.Printf("Failed to increment cache: %v", err)
	}

	return nil
}

func (u *visitUseCase) GetVisitsCount() (int64, error) {
	ctx := context.Background()

	count, err := u.visitCache.Get(ctx)
	if err != nil {
		log.Printf("Cache error: %v, falling back to database", err)
	} else if count > 0 {
		return count, nil
	}

	count, err = u.visitRepo.Count()
	if err != nil {
		return 0, err
	}

	if err := u.visitCache.Set(ctx, count); err != nil {
		log.Printf("Failed to set cache: %v", err)
	}

	return count, nil
}
