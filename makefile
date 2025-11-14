.PHONY: help build run test clean docker-build docker-up docker-down migrate

help: ## Display this help screen
	@echo "Available commands:"
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build the application binary
	@echo "Building application..."
	@CGO_ENABLED=0 go build -ldflags="-w -s" -o bin/api ./cmd/api

run: ## Run the application locally
	@echo "Running application..."
	@go run ./cmd/api

clean: ## Clean build artifacts
	@echo "Cleaning..."
	@rm -rf bin/
	@rm -f coverage.out

docker-build: ## Build Docker image
	@echo "Building Docker image..."
	@docker build -f build/dockerfile -t go-simple-api:latest .

docker-up: ## Start all services with Docker Compose
	@echo "Starting services..."
	@cd deployments && docker-compose up -d

docker-down: ## Stop all services
	@echo "Stopping services..."
	@cd deployments && docker-compose down

docker-logs: ## View Docker logs
	@cd deployments && docker-compose logs -f

migrate: ## Run database migrations
	@echo "Running migrations..."
	@cd deployments && docker-compose up flyway

deps: ## Download dependencies
	@echo "Downloading dependencies..."
	@go mod download
	@go mod tidy

lint: ## Run linter
	@echo "Running linter..."
	@golangci-lint run

fmt: ## Format code
	@echo "Formatting code..."
	@go fmt ./...
	@gofmt -s -w .

vet: ## Run go vet
	@echo "Running go vet..."
	@go vet ./...
