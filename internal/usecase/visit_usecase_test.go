package usecase

import (
	"context"
	"errors"
	"testing"
)

type mockVisitRepository struct {
	createFunc func(ipAddress string) error
	countFunc  func() (int64, error)
}

func (m *mockVisitRepository) Create(ipAddress string) error {
	if m.createFunc != nil {
		return m.createFunc(ipAddress)
	}
	return nil
}

func (m *mockVisitRepository) Count() (int64, error) {
	if m.countFunc != nil {
		return m.countFunc()
	}
	return 0, nil
}

type mockVisitCache struct {
	getFunc        func(ctx context.Context) (int64, error)
	setFunc        func(ctx context.Context, count int64) error
	invalidateFunc func(ctx context.Context) error
	incrementFunc  func(ctx context.Context) error
}

func (m *mockVisitCache) Get(ctx context.Context) (int64, error) {
	if m.getFunc != nil {
		return m.getFunc(ctx)
	}
	return 0, nil
}

func (m *mockVisitCache) Set(ctx context.Context, count int64) error {
	if m.setFunc != nil {
		return m.setFunc(ctx, count)
	}
	return nil
}

func (m *mockVisitCache) Invalidate(ctx context.Context) error {
	if m.invalidateFunc != nil {
		return m.invalidateFunc(ctx)
	}
	return nil
}

func (m *mockVisitCache) Increment(ctx context.Context) error {
	if m.incrementFunc != nil {
		return m.incrementFunc(ctx)
	}
	return nil
}

func TestRecordVisit(t *testing.T) {
	t.Run("Success", func(t *testing.T) {
		repo := &mockVisitRepository{
			createFunc: func(ipAddress string) error {
				return nil
			},
		}
		cache := &mockVisitCache{
			incrementFunc: func(ctx context.Context) error {
				return nil
			},
		}

		uc := NewVisitUseCase(repo, cache)
		err := uc.RecordVisit("192.168.1.1")

		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}
	})

	t.Run("Repository Error", func(t *testing.T) {
		repo := &mockVisitRepository{
			createFunc: func(ipAddress string) error {
				return errors.New("database error")
			},
		}
		cache := &mockVisitCache{}

		uc := NewVisitUseCase(repo, cache)
		err := uc.RecordVisit("192.168.1.1")

		if err == nil {
			t.Error("Expected error, got nil")
		}
	})

	t.Run("Cache Error (should not fail)", func(t *testing.T) {
		repo := &mockVisitRepository{
			createFunc: func(ipAddress string) error {
				return nil
			},
		}
		cache := &mockVisitCache{
			incrementFunc: func(ctx context.Context) error {
				return errors.New("cache error")
			},
		}

		uc := NewVisitUseCase(repo, cache)
		err := uc.RecordVisit("192.168.1.1")

		// Should not fail even if cache fails
		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}
	})
}

func TestGetVisitsCount(t *testing.T) {
	t.Run("Cache Hit", func(t *testing.T) {
		repo := &mockVisitRepository{}
		cache := &mockVisitCache{
			getFunc: func(ctx context.Context) (int64, error) {
				return 100, nil
			},
		}

		uc := NewVisitUseCase(repo, cache)
		count, err := uc.GetVisitsCount()

		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}
		if count != 100 {
			t.Errorf("Expected count 100, got %d", count)
		}
	})

	t.Run("Cache Miss - Get from DB", func(t *testing.T) {
		repo := &mockVisitRepository{
			countFunc: func() (int64, error) {
				return 50, nil
			},
		}
		cache := &mockVisitCache{
			getFunc: func(ctx context.Context) (int64, error) {
				return 0, nil // Cache miss
			},
			setFunc: func(ctx context.Context, count int64) error {
				return nil
			},
		}

		uc := NewVisitUseCase(repo, cache)
		count, err := uc.GetVisitsCount()

		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}
		if count != 50 {
			t.Errorf("Expected count 50, got %d", count)
		}
	})

	t.Run("Cache Error - Fallback to DB", func(t *testing.T) {
		repo := &mockVisitRepository{
			countFunc: func() (int64, error) {
				return 75, nil
			},
		}
		cache := &mockVisitCache{
			getFunc: func(ctx context.Context) (int64, error) {
				return 0, errors.New("cache error")
			},
			setFunc: func(ctx context.Context, count int64) error {
				return nil
			},
		}

		uc := NewVisitUseCase(repo, cache)
		count, err := uc.GetVisitsCount()

		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}
		if count != 75 {
			t.Errorf("Expected count 75, got %d", count)
		}
	})

	t.Run("Database Error", func(t *testing.T) {
		repo := &mockVisitRepository{
			countFunc: func() (int64, error) {
				return 0, errors.New("database error")
			},
		}
		cache := &mockVisitCache{
			getFunc: func(ctx context.Context) (int64, error) {
				return 0, nil // Cache miss
			},
		}

		uc := NewVisitUseCase(repo, cache)
		_, err := uc.GetVisitsCount()

		if err == nil {
			t.Error("Expected error, got nil")
		}
	})
}
