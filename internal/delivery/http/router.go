package http

import (
	"github.com/gin-gonic/gin"
	"github.com/lazarevnik/MCT-2025-containers/internal/domain"
)

func SetupRouter(visitUC domain.VisitUseCase, devMode bool) *gin.Engine {
	router := gin.Default()

	handler := NewHandler(visitUC, devMode)

	router.GET("/ping", handler.Ping)
	router.GET("/visits", handler.Visits)

	return router
}
