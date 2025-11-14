package redis

import (
	"context"
	"testing"
	"time"

	"github.com/go-redis/redismock/v9"
)

func TestGet(t *testing.T) {
	db, mock := redismock.NewClientMock()
	cache := NewVisitCache(db)
	ctx := context.Background()

	t.Run("Success", func(t *testing.T) {
		mock.ExpectGet("visits:count").SetVal("42")

		count, err := cache.Get(ctx)
		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}
		if count != 42 {
			t.Errorf("Expected count 42, got %d", count)
		}

		if err := mock.ExpectationsWereMet(); err != nil {
			t.Errorf("Unfulfilled expectations: %v", err)
		}
	})

	t.Run("Cache Miss", func(t *testing.T) {
		mock.ExpectGet("visits:count").RedisNil()

		count, err := cache.Get(ctx)
		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}
		if count != 0 {
			t.Errorf("Expected count 0, got %d", count)
		}
	})
}

func TestSet(t *testing.T) {
	db, mock := redismock.NewClientMock()
	cache := NewVisitCache(db)
	ctx := context.Background()

	t.Run("Success", func(t *testing.T) {
		mock.ExpectSet("visits:count", int64(42), 10*time.Second).SetVal("OK")

		err := cache.Set(ctx, 42)
		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}

		if err := mock.ExpectationsWereMet(); err != nil {
			t.Errorf("Unfulfilled expectations: %v", err)
		}
	})
}

func TestIncrement(t *testing.T) {
	db, mock := redismock.NewClientMock()
	cache := NewVisitCache(db)
	ctx := context.Background()

	t.Run("Success", func(t *testing.T) {
		mock.ExpectIncr("visits:count").SetVal(1)
		mock.ExpectExpire("visits:count", 10*time.Second).SetVal(true)

		err := cache.Increment(ctx)
		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}

		if err := mock.ExpectationsWereMet(); err != nil {
			t.Errorf("Unfulfilled expectations: %v", err)
		}
	})
}

func TestInvalidate(t *testing.T) {
	db, mock := redismock.NewClientMock()
	cache := NewVisitCache(db)
	ctx := context.Background()

	t.Run("Success", func(t *testing.T) {
		mock.ExpectDel("visits:count").SetVal(1)

		err := cache.Invalidate(ctx)
		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}

		if err := mock.ExpectationsWereMet(); err != nil {
			t.Errorf("Unfulfilled expectations: %v", err)
		}
	})
}
