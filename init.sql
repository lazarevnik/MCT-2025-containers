-- Инициализация базы данных
CREATE TABLE IF NOT EXISTS visits (
    id SERIAL PRIMARY KEY,
    ip VARCHAR(45) NOT NULL,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индекса для улучшения производительности
CREATE INDEX IF NOT EXISTS idx_visits_created_at ON visits(created_at);

-- Комментарий к таблице
COMMENT ON TABLE visits IS 'Таблица для хранения истории посещений';
