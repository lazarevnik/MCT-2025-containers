package http

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

func TestVisitsDevMode(t *testing.T) {
	gin.SetMode(gin.TestMode)

	t.Run("Dev Mode Returns -1", func(t *testing.T) {
		mockUC := &mockVisitUseCase{}

		handler := NewHandler(mockUC, true)
		router := gin.New()
		router.GET("/visits", handler.Visits)

		req, _ := http.NewRequest("GET", "/visits", nil)
		w := httptest.NewRecorder()
		router.ServeHTTP(w, req)

		if w.Code != http.StatusOK {
			t.Errorf("Expected status 200, got %d", w.Code)
		}

		if w.Body.String() != "-1" {
			t.Errorf("Expected '-1' in dev mode, got '%s'", w.Body.String())
		}
	})

	t.Run("Prod Mode Returns Actual Count", func(t *testing.T) {
		mockUC := &mockVisitUseCase{
			getVisitsCountFunc: func() (int64, error) {
				return 42, nil
			},
		}

		handler := NewHandler(mockUC, false) // PROD MODE
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
}
