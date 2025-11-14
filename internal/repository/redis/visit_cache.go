package redis

import (
	"context"
	"errors"
	"fmt"
	"strconv"
	"time"

	"github.com/redis/go-redis/v9"
)

const (
	visitsCountKey = "visits:count"
	cacheTTL       = 10 * time.Second
)

type VisitCache struct {
	client *redis.Client
}

func NewVisitCache(client *redis.Client) *VisitCache {
	return &VisitCache{
		client: client,
	}
}

func (c *VisitCache) Get(ctx context.Context) (int64, error) {
	val, err := c.client.Get(ctx, visitsCountKey).Result()
	if errors.Is(err, redis.Nil) {
		return 0, nil
	}
	if err != nil {
		return 0, fmt.Errorf("failed to get from cache: %w", err)
	}

	count, err := strconv.ParseInt(val, 10, 64)
	if err != nil {
		return 0, fmt.Errorf("failed to parse cached value: %w", err)
	}

	return count, nil
}

func (c *VisitCache) Set(ctx context.Context, count int64) error {
	err := c.client.Set(ctx, visitsCountKey, count, cacheTTL).Err()
	if err != nil {
		return fmt.Errorf("failed to set cache: %w", err)
	}
	return nil
}

func (c *VisitCache) Invalidate(ctx context.Context) error {
	err := c.client.Del(ctx, visitsCountKey).Err()
	if err != nil {
		return fmt.Errorf("failed to invalidate cache: %w", err)
	}
	return nil
}

func (c *VisitCache) Increment(ctx context.Context) error {
	err := c.client.Incr(ctx, visitsCountKey).Err()
	if err != nil {
		return fmt.Errorf("failed to increment cache: %w", err)
	}
	c.client.Expire(ctx, visitsCountKey, cacheTTL)
	return nil
}
