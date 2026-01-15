"""Environment variable constants for SQLAlchemy adapter configuration."""

# Database connection URL (e.g., postgresql://user:pass@host/db, sqlite:///path.db)
SQLALCHEMY_DATABASE_URL = "SQLALCHEMY_DATABASE_URL"

# Enable SQL statement logging
SQLALCHEMY_ECHO = "SQLALCHEMY_ECHO"

# Connection pool size (default: 5)
SQLALCHEMY_POOL_SIZE = "SQLALCHEMY_POOL_SIZE"

# Connection pool timeout in seconds (default: 30)
SQLALCHEMY_POOL_TIMEOUT = "SQLALCHEMY_POOL_TIMEOUT"

# Connection recycle time in seconds (default: 3600)
SQLALCHEMY_POOL_RECYCLE = "SQLALCHEMY_POOL_RECYCLE"

# Pre-ping connections before use (default: True)
SQLALCHEMY_POOL_PRE_PING = "SQLALCHEMY_POOL_PRE_PING"

# Maximum overflow connections (default: 10)
SQLALCHEMY_MAX_OVERFLOW = "SQLALCHEMY_MAX_OVERFLOW"
