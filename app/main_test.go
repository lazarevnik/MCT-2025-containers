package app

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	"github.com/redis/go-redis/v9"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func setupTestDB(t *testing.T) *gorm.DB {
	dsn := fmt.Sprintf("user=%s password=%s host=%s port=%s dbname=%s sslmode=disable",
		os.Getenv("DB_USER"),
		os.Getenv("DB_PASSWORD"),
		os.Getenv("DB_HOST"),
		os.Getenv("DB_PORT"),
		os.Getenv("DB_NAME"),
	)

	testDB, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		t.Fatalf("Failed to connect to test database: %v", err)
	}

	if err := testDB.AutoMigrate(&Visit{}); err != nil {
		t.Fatalf("Failed to migrate test database: %v", err)
	}

	return testDB
}

func setupTestRedis(t *testing.T) *redis.Client {
	testRdb := redis.NewClient(&redis.Options{
		Addr: os.Getenv("REDIS_ADDR"),
	})

	if err := testRdb.Ping(context.Background()).Err(); err != nil {
		t.Fatalf("Failed to connect to test redis: %v", err)
	}

	return testRdb
}

func TestGetClientIP(t *testing.T) {
	tests := []struct {
		name       string
		headers    map[string]string
		remoteAddr string
		expected   string
	}{
		{
			name:       "X-Forwarded-For header",
			headers:    map[string]string{"X-Forwarded-For": "192.168.1.1"},
			remoteAddr: "127.0.0.1:8080",
			expected:   "192.168.1.1",
		},
		{
			name:       "X-Real-IP header",
			headers:    map[string]string{"X-Real-IP": "10.0.0.1"},
			remoteAddr: "127.0.0.1:8080",
			expected:   "10.0.0.1",
		},
		{
			name:       "RemoteAddr fallback",
			headers:    map[string]string{},
			remoteAddr: "172.16.0.1:9090",
			expected:   "172.16.0.1",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/test", nil)
			for k, v := range tt.headers {
				req.Header.Set(k, v)
			}
			req.RemoteAddr = tt.remoteAddr

			got := getClientIP(req)
			if got != tt.expected {
				t.Errorf("getClientIP() = %q, want %q", got, tt.expected)
			}
		})
	}
}

func TestHandlePing(t *testing.T) {
	if os.Getenv("SKIP_INTEGRATION_TESTS") == "true" {
		t.Skip("Skipping integration tests")
	}

	db = setupTestDB(t)
	rdb = setupTestRedis(t)

	db.Exec("DELETE FROM visits")
	rdb.Del(context.Background(), "visits_count")

	err := os.Setenv("ENV", "prod")
	if err != nil {
		t.Errorf("Failed to set ENV environment variable: %v", err)
	}

	req := httptest.NewRequest("GET", "/ping", nil)
	req.Header.Set("X-Forwarded-For", "192.168.1.1")
	w := httptest.NewRecorder()

	handlePing(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("handlePing() status code = %d, want %d", w.Code, http.StatusOK)
	}

	if w.Body.String() != "pong" {
		t.Errorf("handlePing() body = %q, want %q", w.Body.String(), "pong")
	}

	var count int64
	if err := db.Model(&Visit{}).Count(&count).Error; err != nil {
		t.Errorf("Failed to count visits: %v", err)
	}

	if count != 1 {
		t.Errorf("Expected 1 visit, got %d", count)
	}
}

func TestHandleVisits(t *testing.T) {
	if os.Getenv("SKIP_INTEGRATION_TESTS") == "true" {
		t.Skip("Skipping integration tests")
	}

	db = setupTestDB(t)
	rdb = setupTestRedis(t)

	// Clear test data
	db.Exec("DELETE FROM visits")
	rdb.Del(context.Background(), "visits_count")

	err := os.Setenv("ENV", "prod")
	if err != nil {
		t.Errorf("Failed to set ENV environment variable: %v", err)
	}

	// Create some test visits
	for i := 0; i < 3; i++ {
		db.Create(&Visit{IP: "192.168.1.1"})
	}

	req := httptest.NewRequest("GET", "/visits", nil)
	w := httptest.NewRecorder()

	handleVisits(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("handleVisits() status code = %d, want %d", w.Code, http.StatusOK)
	}

	if w.Body.String() != "3" {
		t.Errorf("handleVisits() body = %q, want %q", w.Body.String(), "3")
	}

	// Verify cache was set
	val, err := rdb.Get(context.Background(), "visits_count").Result()
	if err != nil {
		t.Errorf("Cache not set: %v", err)
	}

	if val != "3" {
		t.Errorf("Cache value = %q, want %q", val, "3")
	}
}

func TestHandleVisitsDevMode(t *testing.T) {
	if os.Getenv("SKIP_INTEGRATION_TESTS") == "true" {
		t.Skip("Skipping integration tests")
	}

	db = setupTestDB(t)
	rdb = setupTestRedis(t)

	os.Setenv("DEV_MODE", "true")

	req := httptest.NewRequest("GET", "/visits", nil)
	w := httptest.NewRecorder()

	handleVisits(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("handleVisits() in dev mode status code = %d, want %d", w.Code, http.StatusOK)
	}

	if w.Body.String() != "-1" {
		t.Errorf("handleVisits() in dev mode body = %q, want %q", w.Body.String(), "-1")
	}
}

func TestCacheConsistency(t *testing.T) {
	if os.Getenv("SKIP_INTEGRATION_TESTS") == "true" {
		t.Skip("Skipping integration tests")
	}

	db = setupTestDB(t)
	rdb = setupTestRedis(t)

	// Clear test data
	db.Exec("DELETE FROM visits")
	rdb.Del(context.Background(), "visits_count")

	err := os.Setenv("ENV", "prod")
	if err != nil {
		t.Errorf("Failed to set ENV environment variable: %v", err)
	}

	// Add visits
	for i := 0; i < 5; i++ {
		db.Create(&Visit{IP: "192.168.1.1"})
	}

	// First request (cache miss, queries DB)
	req1 := httptest.NewRequest("GET", "/visits", nil)
	w1 := httptest.NewRecorder()
	handleVisits(w1, req1)

	// Second request (cache hit)
	req2 := httptest.NewRequest("GET", "/visits", nil)
	w2 := httptest.NewRecorder()
	handleVisits(w2, req2)

	if w1.Body.String() != w2.Body.String() {
		t.Errorf("Cache consistency failed: %q != %q", w1.Body.String(), w2.Body.String())
	}

	if w1.Body.String() != "5" {
		t.Errorf("Expected 5 visits, got %q", w1.Body.String())
	}
}
