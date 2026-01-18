-- Initialize database with proper charset and collation
ALTER DATABASE ra_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grant permissions
GRANT ALL PRIVILEGES ON ra_agent.* TO 'ra_user'@'%';
FLUSH PRIVILEGES;
