package postgres

import (
	"context"
	"errors"
	"fmt"

	"d4y2k.me/go-simple-api/internal/config"
	"d4y2k.me/go-simple-api/internal/domain"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type VisitRepository struct {
	pool *pgxpool.Pool
}

func NewVisitRepository(cfg *config.DatabaseConfig) (*VisitRepository, error) {
	poolConfig, err := pgxpool.ParseConfig(cfg.DSN())
	if err != nil {
		return nil, fmt.Errorf("failed to parse database config: %w", err)
	}

	poolConfig.MaxConns = cfg.MaxConns
	poolConfig.MinConns = cfg.MinConns
	poolConfig.MaxConnLifetime = cfg.MaxConnLifetime
	poolConfig.MaxConnIdleTime = cfg.MaxConnIdleTime

	ctx := context.Background()
	pool, err := pgxpool.NewWithConfig(ctx, poolConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create connection pool: %w", err)
	}

	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return &VisitRepository{pool: pool}, nil
}

func (r *VisitRepository) IncrementVisit(ctx context.Context, ip string) error {
	query := `
		INSERT INTO visits (ip, count, created_at, updated_at)
		VALUES ($1, 1, NOW(), NOW())
		ON CONFLICT (ip)
		DO UPDATE SET
			count = visits.count + 1,
			updated_at = NOW()
	`

	_, err := r.pool.Exec(ctx, query, ip)
	if err != nil {
		return fmt.Errorf("failed to increment visit: %w", err)
	}

	return nil
}

func (r *VisitRepository) GetVisitCount(ctx context.Context, ip string) (int64, error) {
	query := `SELECT count FROM visits WHERE ip = $1`

	var count int64
	err := r.pool.QueryRow(ctx, query, ip).Scan(&count)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return 0, domain.ErrNotFound
		}
		return 0, fmt.Errorf("failed to get visit count: %w", err)
	}

	return count, nil
}

func (r *VisitRepository) GetAllVisits(ctx context.Context) ([]domain.Visit, error) {
	query := `
		SELECT id, ip, count, created_at, updated_at
		FROM visits
		ORDER BY count DESC, updated_at DESC
	`

	rows, err := r.pool.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to query visits: %w", err)
	}
	defer rows.Close()

	var visits []domain.Visit
	for rows.Next() {
		var v domain.Visit
		if err := rows.Scan(&v.ID, &v.IP, &v.Count, &v.CreatedAt, &v.UpdatedAt); err != nil {
			return nil, fmt.Errorf("failed to scan visit: %w", err)
		}
		visits = append(visits, v)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating visits: %w", err)
	}

	return visits, nil
}

func (r *VisitRepository) Close() error {
	r.pool.Close()
	return nil
}
