package config

import (
	"os"
	"testing"
)

func TestLoad(t *testing.T) {
	t.Run("Default Values", func(t *testing.T) {
		cfg := Load()

		if cfg.Server.Port != "5000" {
			t.Errorf("Expected default port 5000, got %s", cfg.Server.Port)
		}

		if cfg.Database.Host != "localhost" {
			t.Errorf("Expected default DB host localhost, got %s", cfg.Database.Host)
		}

		if cfg.Redis.Addr != "localhost:6379" {
			t.Errorf("Expected default Redis addr localhost:6379, got %s", cfg.Redis.Addr)
		}
	})

	t.Run("Environment Variables", func(t *testing.T) {
		os.Setenv("SERVER_PORT", "8080")
		os.Setenv("DB_HOST", "testhost")
		os.Setenv("REDIS_ADDR", "redis:6379")

		cfg := Load()

		if cfg.Server.Port != "8080" {
			t.Errorf("Expected port 8080, got %s", cfg.Server.Port)
		}

		if cfg.Database.Host != "testhost" {
			t.Errorf("Expected DB host testhost, got %s", cfg.Database.Host)
		}

		if cfg.Redis.Addr != "redis:6379" {
			t.Errorf("Expected Redis addr redis:6379, got %s", cfg.Redis.Addr)
		}

		os.Unsetenv("SERVER_PORT")
		os.Unsetenv("DB_HOST")
		os.Unsetenv("REDIS_ADDR")
	})
}

func TestGetEnv(t *testing.T) {
	t.Run("Existing Variable", func(t *testing.T) {
		os.Setenv("TEST_VAR", "test_value")
		value := getEnv("TEST_VAR", "default")
		os.Unsetenv("TEST_VAR")

		if value != "test_value" {
			t.Errorf("Expected 'test_value', got '%s'", value)
		}
	})

	t.Run("Missing Variable", func(t *testing.T) {
		value := getEnv("MISSING_VAR", "default_value")

		if value != "default_value" {
			t.Errorf("Expected 'default_value', got '%s'", value)
		}
	})
}
