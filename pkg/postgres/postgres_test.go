package postgres

import (
	"testing"

	"github.com/lazarevnik/MCT-2025-containers/config"
)

func TestNewPostgresDB(t *testing.T) {
	t.Run("Invalid Connection", func(t *testing.T) {
		cfg := config.DatabaseConfig{
			Host:     "invalid-host",
			Port:     "9999",
			User:     "test",
			Password: "test",
			DBName:   "test",
			SSLMode:  "disable",
		}

		_, err := NewPostgresDB(cfg)
		if err == nil {
			t.Error("Expected error for invalid connection, got nil")
		}
	})
}
