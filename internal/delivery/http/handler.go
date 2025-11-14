package http

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/lazarevnik/MCT-2025-containers/internal/domain"
)

type Handler struct {
	visitUC domain.VisitUseCase
	devMode bool
}

func NewHandler(visitUC domain.VisitUseCase, devMode bool) *Handler {
	return &Handler{
		visitUC: visitUC,
		devMode: devMode,
	}
}

func (h *Handler) Ping(c *gin.Context) {
	clientIP := c.ClientIP()

	if err := h.visitUC.RecordVisit(clientIP); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to record visit"})
		return
	}

	c.String(http.StatusOK, "pong")
}

func (h *Handler) Visits(c *gin.Context) {
	if h.devMode {
		c.String(http.StatusOK, "-1")
		return
	}

	count, err := h.visitUC.GetVisitsCount()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get visits count"})
		return
	}

	c.String(http.StatusOK, "%d", count)
}
