package postgres

import (
	"database/sql"
	"fmt"
	"time"

	"github.com/lazarevnik/MCT-2025-containers/config"
	_ "github.com/lib/pq"
)

type DB = sql.DB

func NewPostgresDB(cfg config.DatabaseConfig) (*DB, error) {
	dsn := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=%s",
		cfg.Host, cfg.Port, cfg.User, cfg.Password, cfg.DBName, cfg.SSLMode)

	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("error opening database: %w", err)
	}

	db.SetMaxOpenConns(22)
	db.SetMaxIdleConns(2)
	db.SetConnMaxLifetime(8 * time.Minute)

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("error connecting to the database: %w", err)
	}

	return db, nil
}
