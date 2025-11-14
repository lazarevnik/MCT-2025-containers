package http

import (
	"testing"

	"github.com/gin-gonic/gin"
)

func TestSetupRouter(t *testing.T) {
	gin.SetMode(gin.TestMode)

	t.Run("Routes Configured", func(t *testing.T) {
		mockUC := &mockVisitUseCase{}
		router := SetupRouter(mockUC, false)

		routes := router.Routes()
		if len(routes) < 2 {
			t.Errorf("Expected at least 2 routes, got %d", len(routes))
		}

		foundPing := false
		foundVisits := false
		for _, route := range routes {
			if route.Path == "/ping" && route.Method == "GET" {
				foundPing = true
			}
			if route.Path == "/visits" && route.Method == "GET" {
				foundVisits = true
			}
		}

		if !foundPing {
			t.Error("Route /ping not found")
		}
		if !foundVisits {
			t.Error("Route /visits not found")
		}
	})
}
