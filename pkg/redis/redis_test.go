package redis

import (
	"testing"
)

func TestNewRedisClient(t *testing.T) {
	t.Run("Invalid Connection", func(t *testing.T) {
		_, err := NewRedisClient("invalid-host:9999", "", 0)
		if err == nil {
			t.Error("Expected error for invalid connection, got nil")
		}
	})
}
