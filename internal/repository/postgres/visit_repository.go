package postgres

import (
	"database/sql"

	"github.com/lazarevnik/MCT-2025-containers/internal/domain"
)

type visitRepository struct {
	db *sql.DB
}

func NewVisitRepository(db *sql.DB) domain.VisitRepository {
	return &visitRepository{db: db}
}

func (r *visitRepository) Create(ipAddress string) error {
	query := `INSERT INTO visits (ip_address) VALUES ($1)`
	_, err := r.db.Exec(query, ipAddress)
	return err
}

func (r *visitRepository) Count() (int64, error) {
	var count int64
	query := `SELECT COUNT(*) FROM visits`
	err := r.db.QueryRow(query).Scan(&count)
	if err != nil {
		return 0, err
	}
	return count, nil
}

