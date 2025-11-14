package handler

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"strings"

	"d4y2k.me/go-simple-api/internal/service"
)

type VisitHandler struct {
	visitService *service.VisitService
	logger       *slog.Logger
}

func NewVisitHandler(visitService *service.VisitService, logger *slog.Logger) *VisitHandler {
	return &VisitHandler{
		visitService: visitService,
		logger:       logger,
	}
}

type PingResponse struct {
	Message string `json:"message"`
}

type VisitsResponse struct {
	IP    string `json:"ip"`
	Count int64  `json:"count"`
}

type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message,omitempty"`
}

func (h *VisitHandler) HandlePing(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	ip := getClientIP(r)

	if err := h.visitService.RecordPing(ctx, ip); err != nil {
		h.logger.Error("failed to record ping", "error", err, "ip", ip)
		h.sendError(w, "Failed to record visit", http.StatusInternalServerError)
		return
	}

	h.logger.Info("ping recorded", "ip", ip)

	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("pong"))
}

func (h *VisitHandler) HandleVisits(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	ip := getClientIP(r)

	count, err := h.visitService.GetVisitCount(ctx, ip)
	if err != nil {
		h.logger.Error("failed to get visit count", "error", err, "ip", ip)
		h.sendError(w, "Failed to get visit count", http.StatusInternalServerError)
		return
	}

	h.logger.Info("visit count retrieved", "ip", ip, "count", count)

	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, "%d", count)
}

func getClientIP(r *http.Request) string {
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		ips := strings.Split(xff, ",")
		if len(ips) > 0 {
			return strings.TrimSpace(ips[0])
		}
	}

	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		return xri
	}

	ip := r.RemoteAddr
	if colon := strings.LastIndex(ip, ":"); colon != -1 {
		ip = ip[:colon]
	}

	return ip
}

func (h *VisitHandler) sendJSON(w http.ResponseWriter, data interface{}, statusCode int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)

	if err := json.NewEncoder(w).Encode(data); err != nil {
		h.logger.Error("failed to encode JSON response", "error", err)
	}
}

func (h *VisitHandler) sendError(w http.ResponseWriter, message string, statusCode int) {
	h.sendJSON(w, ErrorResponse{
		Error:   http.StatusText(statusCode),
		Message: message,
	}, statusCode)
}
