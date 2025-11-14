package http

import (
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

type mockVisitUseCase struct {
	recordVisitFunc    func(ipAddress string) error
	getVisitsCountFunc func() (int64, error)
}

func (m *mockVisitUseCase) RecordVisit(ipAddress string) error {
	if m.recordVisitFunc != nil {
		return m.recordVisitFunc(ipAddress)
	}
	return nil
}

func (m *mockVisitUseCase) GetVisitsCount() (int64, error) {
	if m.getVisitsCountFunc != nil {
		return m.getVisitsCountFunc()
	}
	return 0, nil
}

func TestPing(t *testing.T) {
	gin.SetMode(gin.TestMode)

	t.Run("Success", func(t *testing.T) {
		mockUC := &mockVisitUseCase{
			recordVisitFunc: func(ipAddress string) error {
				return nil
			},
		}

		handler := NewHandler(mockUC, false)
		router := gin.New()
		router.GET("/ping", handler.Ping)

		req, _ := http.NewRequest("GET", "/ping", nil)
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		if w.Code != http.StatusOK {
			t.Errorf("Expected status 200, got %d", w.Code)
		}

		if w.Body.String() != "pong" {
			t.Errorf("Expected 'pong', got '%s'", w.Body.String())
		}
	})

	t.Run("Error Recording Visit", func(t *testing.T) {
		mockUC := &mockVisitUseCase{
			recordVisitFunc: func(ipAddress string) error {
				return errors.New("database error")
			},
		}

		handler := NewHandler(mockUC, false)
		router := gin.New()
		router.GET("/ping", handler.Ping)

		req, _ := http.NewRequest("GET", "/ping", nil)
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		if w.Code != http.StatusInternalServerError {
			t.Errorf("Expected status 500, got %d", w.Code)
		}
	})
}

func TestVisits(t *testing.T) {
	gin.SetMode(gin.TestMode)

	t.Run("Success", func(t *testing.T) {
		mockUC := &mockVisitUseCase{
			getVisitsCountFunc: func() (int64, error) {
				return 42, nil
			},
		}

		handler := NewHandler(mockUC, false)
		router := gin.New()
		router.GET("/visits", handler.Visits)

		req, _ := http.NewRequest("GET", "/visits", nil)
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		if w.Code != http.StatusOK {
			t.Errorf("Expected status 200, got %d", w.Code)
		}

		if w.Body.String() != "42" {
			t.Errorf("Expected '42', got '%s'", w.Body.String())
		}
	})

	t.Run("Error Getting Count", func(t *testing.T) {
		mockUC := &mockVisitUseCase{
			getVisitsCountFunc: func() (int64, error) {
				return 0, errors.New("database error")
			},
		}

		handler := NewHandler(mockUC, false)
		router := gin.New()
		router.GET("/visits", handler.Visits)

		req, _ := http.NewRequest("GET", "/visits", nil)
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		if w.Code != http.StatusInternalServerError {
			t.Errorf("Expected status 500, got %d", w.Code)
		}
	})
}
