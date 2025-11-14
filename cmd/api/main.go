package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"d4y2k.me/go-simple-api/internal/config"
	"d4y2k.me/go-simple-api/internal/handler"
	"d4y2k.me/go-simple-api/internal/repository/postgres"
	"d4y2k.me/go-simple-api/internal/repository/redis"
	"d4y2k.me/go-simple-api/internal/service"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))
	slog.SetDefault(logger)

	cfg, err := config.Load()
	if err != nil {
		logger.Error("failed to load config", "error", err)
		os.Exit(1)
	}

	if err := run(cfg, logger); err != nil {
		logger.Error("application failed", "error", err)
		os.Exit(1)
	}
}

func run(cfg *config.Config, logger *slog.Logger) error {
	visitRepo, err := postgres.NewVisitRepository(&cfg.Database)
	if err != nil {
		return err
	}
	defer func() {
		if err := visitRepo.Close(); err != nil {
			logger.Error("failed to close visit repository", "error", err)
		}
	}()
	logger.Info("connected to PostgreSQL", "host", cfg.Database.Host)

	cacheRepo, err := redis.NewCacheRepository(&cfg.Redis)
	if err != nil {
		return err
	}
	defer func() {
		if err := cacheRepo.Close(); err != nil {
			logger.Error("failed to close cache repository", "error", err)
		}
	}()
	logger.Info("connected to Redis", "host", cfg.Redis.Host)

	visitService := service.NewVisitService(visitRepo, cacheRepo)
	visitHandler := handler.NewVisitHandler(visitService, logger)

	router := handler.NewRouter(visitHandler, logger)

	srv := &http.Server{
		Addr:         cfg.Server.Address(),
		Handler:      router,
		ReadTimeout:  cfg.Server.ReadTimeout,
		WriteTimeout: cfg.Server.WriteTimeout,
		IdleTimeout:  120 * time.Second,
	}

	serverErrors := make(chan error, 1)
	go func() {
		logger.Info("starting server", "address", srv.Addr)
		serverErrors <- srv.ListenAndServe()
	}()

	shutdown := make(chan os.Signal, 1)
	signal.Notify(shutdown, os.Interrupt, syscall.SIGTERM)

	select {
	case err := <-serverErrors:
		if err != nil && !errors.Is(err, http.ErrServerClosed) {
			return err
		}
	case sig := <-shutdown:
		logger.Info("shutdown signal received", "signal", sig.String())

		ctx, cancel := context.WithTimeout(context.Background(), cfg.Server.ShutdownTimeout)
		defer cancel()

		if err := srv.Shutdown(ctx); err != nil {
			logger.Error("graceful shutdown failed", "error", err)
			if err := srv.Close(); err != nil {
				return err
			}
		}
		logger.Info("server stopped gracefully")
	}

	return nil
}
