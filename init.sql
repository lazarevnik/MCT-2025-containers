CREATE TABLE IF NOT EXISTS ping_requests (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL,
    request_time TIMESTAMP NOT NULL DEFAULT NOW()
);
