package postgres

import (
	"testing"

	"github.com/DATA-DOG/go-sqlmock"
)

func TestCreate(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("Failed to create mock: %v", err)
	}
	defer db.Close()

	repo := NewVisitRepository(db)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectExec("INSERT INTO visits").
			WithArgs("192.168.1.1").
			WillReturnResult(sqlmock.NewResult(1, 1))

		err := repo.Create("192.168.1.1")
		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}

		if err := mock.ExpectationsWereMet(); err != nil {
			t.Errorf("Unfulfilled expectations: %v", err)
		}
	})

	t.Run("Error", func(t *testing.T) {
		mock.ExpectExec("INSERT INTO visits").
			WithArgs("192.168.1.1").
			WillReturnError(sqlmock.ErrCancelled)

		err := repo.Create("192.168.1.1")
		if err == nil {
			t.Error("Expected error, got nil")
		}
	})
}

func TestCount(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("Failed to create mock: %v", err)
	}
	defer db.Close()

	repo := NewVisitRepository(db)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"count"}).AddRow(42)
		mock.ExpectQuery("SELECT COUNT").WillReturnRows(rows)

		count, err := repo.Count()
		if err != nil {
			t.Errorf("Expected no error, got %v", err)
		}
		if count != 42 {
			t.Errorf("Expected count 42, got %d", count)
		}

		if err := mock.ExpectationsWereMet(); err != nil {
			t.Errorf("Unfulfilled expectations: %v", err)
		}
	})

	t.Run("Error", func(t *testing.T) {
		mock.ExpectQuery("SELECT COUNT").WillReturnError(sqlmock.ErrCancelled)

		_, err := repo.Count()
		if err == nil {
			t.Error("Expected error, got nil")
		}
	})
}
