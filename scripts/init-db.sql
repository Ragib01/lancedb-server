-- LanceDB Server Database Initialization
-- This script creates initial database objects and default admin user

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The tables will be created by SQLAlchemy/Alembic
-- This script can contain any additional setup

-- Insert default admin API key if not exists
-- Note: This would normally be done through the API, but we'll create a placeholder
-- The actual key generation should be done via the API endpoints 