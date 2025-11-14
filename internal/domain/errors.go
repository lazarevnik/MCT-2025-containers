package domain

import "errors"

var (
	ErrNotFound = errors.New("resource not found")

	ErrInvalidInput = errors.New("invalid input")

	ErrInternal = errors.New("internal server error")

	ErrCacheMiss = errors.New("cache miss")
)
