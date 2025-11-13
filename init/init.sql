CREATE TABLE IF NOT EXISTS visits (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_visits_created_at ON visits(created_at);

INSERT INTO visits (ip_address) VALUES ('init_script') 
ON CONFLICT DO NOTHING;

SELECT 'Database initialized successfully' as message;
