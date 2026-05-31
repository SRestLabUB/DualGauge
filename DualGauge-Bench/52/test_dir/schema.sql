-- MySQL schema for users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert test users
INSERT INTO users (username, email) VALUES 
    ('john_doe', 'john@example.com'),
    ('ADMIN', 'admin@example.com'),
    ('user_with_123', 'user123@example.com'),
    ('user.with.dots', 'dots@example.com'),
    ('user-with-dashes', 'dashes@example.com'),
    ('a', 'a@example.com'),
    ('émily_ñoël', 'emily@example.com')
ON DUPLICATE KEY UPDATE email=VALUES(email);
