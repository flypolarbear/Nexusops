-- NexusOps Database Initialization

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    git_repo VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active',
    production_version_id VARCHAR(50),
    extra_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Versions table
CREATE TABLE IF NOT EXISTS versions (
    id VARCHAR(50) PRIMARY KEY,
    project_id VARCHAR(50) NOT NULL REFERENCES projects(id),
    codename VARCHAR(100) NOT NULL,
    version VARCHAR(50),
    git_branch VARCHAR(255),
    git_commit VARCHAR(50),
    status VARCHAR(20) DEFAULT 'building',
    health VARCHAR(20) DEFAULT 'unknown',
    test_url VARCHAR(255),
    deployed_regions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Deployments table
CREATE TABLE IF NOT EXISTS deployments (
    id VARCHAR(50) PRIMARY KEY,
    version_id VARCHAR(50) NOT NULL REFERENCES versions(id),
    region VARCHAR(50) NOT NULL,
    namespace VARCHAR(100) DEFAULT 'default',
    status VARCHAR(20) DEFAULT 'pending',
    health VARCHAR(20) DEFAULT 'unknown',
    argocd_app VARCHAR(255),
    argocd_sync_status VARCHAR(50),
    argocd_health_status VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Deployment steps table
CREATE TABLE IF NOT EXISTS deployment_steps (
    id VARCHAR(50) PRIMARY KEY,
    deployment_id VARCHAR(50) NOT NULL REFERENCES deployments(id),
    step_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    details JSONB
);

-- Agent states table
CREATE TABLE IF NOT EXISTS agent_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(255) NOT NULL,
    agent_version VARCHAR(50),
    conversation_id VARCHAR(255) NOT NULL,
    request_id VARCHAR(255),
    state_type VARCHAR(50) NOT NULL,
    state_key VARCHAR(255) NOT NULL,
    state_value JSONB NOT NULL,
    related_resource_type VARCHAR(50),
    related_resource_id VARCHAR(255),
    version_id VARCHAR(50) REFERENCES versions(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    UNIQUE(agent_id, conversation_id, state_key)
);

-- Agent invocations table
CREATE TABLE IF NOT EXISTS agent_invocations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(255) NOT NULL,
    request_id VARCHAR(255) NOT NULL,
    conversation_id VARCHAR(255),
    request JSONB,
    response JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    latency_ms INTEGER,
    tokens_used INTEGER,
    error_code VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agents table (Agent Registry)
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    manifest JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    endpoint VARCHAR(255),
    last_heartbeat TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    tenant_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Regions table
CREATE TABLE IF NOT EXISTS regions (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    country VARCHAR(100),
    continent VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    k8s_cluster VARCHAR(255),
    k8s_context VARCHAR(255),
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_versions_project ON versions(project_id);
CREATE INDEX IF NOT EXISTS idx_deployments_version ON deployments(version_id);
CREATE INDEX IF NOT EXISTS idx_deployments_region ON deployments(region);
CREATE INDEX IF NOT EXISTS idx_deployment_steps_deployment ON deployment_steps(deployment_id);
CREATE INDEX IF NOT EXISTS idx_agent_states_agent_conv ON agent_states(agent_id, conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_invocations_agent ON agent_invocations(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_invocations_created ON agent_invocations(created_at);

-- Insert sample data

-- Sample projects
INSERT INTO projects (id, name, description, git_repo, status) VALUES
('proj-demo', 'Demo Project', 'A demo project for testing', 'https://github.com/demo/project', 'active')
ON CONFLICT (id) DO NOTHING;

-- Sample versions
INSERT INTO versions (id, project_id, codename, version, git_branch, status, health, test_url) VALUES
('ver-phoenix', 'proj-demo', 'Phoenix', 'v1.2.3', 'main', 'testing', 'healthy', 'https://phoenix.test.example.com'),
('ver-titan', 'proj-demo', 'Titan', 'v1.1.0', 'main', 'production', 'healthy', 'https://titan.example.com')
ON CONFLICT (id) DO NOTHING;

-- Update project production version
UPDATE projects SET production_version_id = 'ver-titan' WHERE id = 'proj-demo';

-- Sample regions
INSERT INTO regions (id, name, code, country, continent, latitude, longitude) VALUES
('us-east', 'US East', 'us-east-1', 'United States', 'North America', 39.0438, -77.4875),
('eu-west', 'EU West', 'eu-west-1', 'Ireland', 'Europe', 53.1424, -7.6921),
('ap-south', 'Asia Pacific South', 'ap-south-1', 'Singapore', 'Asia', 1.3521, 103.8198)
ON CONFLICT (code) DO NOTHING;

-- Sample user
INSERT INTO users (id, username, email, hashed_password, full_name, is_admin) VALUES
('user-admin', 'admin', 'admin@example.com', '$2b$12$dummy_hash', 'Admin User', TRUE)
ON CONFLICT (username) DO NOTHING;
