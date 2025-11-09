-- Migration: Add datasets and events metadata tables
-- Description: Core tables for flexible event schema and dataset management
-- Version: 001
-- Date: 2025-11-08

-- Dataset registry with flexible schema configuration
CREATE TABLE IF NOT EXISTS datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Flexible column mapping configuration
    column_mapping JSONB NOT NULL,
    -- Expected structure: {
    --   "user_column": "customer_id",
    --   "item_column": "product_id",
    --   "timestamp_column": "event_time",
    --   "session_column": "session_id" (optional),
    --   "target_column": "purchased" (optional)
    -- }

    -- Session detection configuration
    session_config JSONB NOT NULL DEFAULT '{"auto_detect": true, "timeout_minutes": 30}'::jsonb,
    -- Expected structure: {
    --   "auto_detect": true,
    --   "timeout_minutes": 30
    -- }

    -- Statistics
    upload_count INTEGER DEFAULT 0,
    total_events BIGINT DEFAULT 0,
    total_sessions BIGINT DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    unique_items INTEGER DEFAULT 0,

    -- Status
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'processing')),

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_upload_at TIMESTAMP,

    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_datasets_tenant ON datasets(tenant_id);
CREATE INDEX idx_datasets_status ON datasets(status);
CREATE INDEX idx_datasets_updated ON datasets(updated_at DESC);

-- Upload history with detailed tracking
CREATE TABLE IF NOT EXISTS dataset_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- File information
    filename VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT,
    s3_path VARCHAR(512) NOT NULL,

    -- Processing results
    row_count INTEGER NOT NULL,
    accepted INTEGER NOT NULL DEFAULT 0,
    rejected INTEGER NOT NULL DEFAULT 0,
    validation_errors JSONB,
    -- Expected structure: [
    --   {"row": 42, "error": "Missing timestamp", "column": "event_time"}
    -- ]

    -- Status
    status VARCHAR(50) DEFAULT 'completed' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,

    -- Processing time
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    processing_duration_ms INTEGER,

    -- Timestamps
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    uploaded_by UUID REFERENCES users(id),
    notes TEXT
);

CREATE INDEX idx_dataset_uploads_dataset ON dataset_uploads(dataset_id);
CREATE INDEX idx_dataset_uploads_tenant ON dataset_uploads(tenant_id);
CREATE INDEX idx_dataset_uploads_status ON dataset_uploads(status);
CREATE INDEX idx_dataset_uploads_date ON dataset_uploads(uploaded_at DESC);

-- Events metadata for fast aggregations and queries
CREATE TABLE IF NOT EXISTS events_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- Partition information
    partition_date DATE NOT NULL,
    partition_path VARCHAR(512) NOT NULL,

    -- Counts
    event_count INTEGER NOT NULL,
    unique_users INTEGER NOT NULL,
    unique_items INTEGER NOT NULL,
    session_count INTEGER,

    -- Statistics (JSONB for flexibility)
    stats JSONB,
    -- Expected structure: {
    --   "avg_session_length": 5.2,
    --   "median_session_duration_minutes": 12.5,
    --   "top_items": [{"item_id": "X", "count": 100}, ...],
    --   "top_users": [{"user_id": "Y", "count": 50}, ...],
    --   "hourly_distribution": {0: 50, 1: 30, ..., 23: 100},
    --   "item_category_distribution": {"electronics": 500, "clothing": 300}
    -- }

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(dataset_id, partition_date)
);

CREATE INDEX idx_events_metadata_dataset ON events_metadata(dataset_id);
CREATE INDEX idx_events_metadata_tenant ON events_metadata(tenant_id);
CREATE INDEX idx_events_metadata_date ON events_metadata(partition_date DESC);

-- User session state for real-time inference
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    -- User identification
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),

    -- Sequence data
    recent_items JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- Expected structure: [
    --   {"item_id": "A", "timestamp": "2025-11-08T10:00:00", "position": 1},
    --   {"item_id": "B", "timestamp": "2025-11-08T10:05:00", "position": 2}
    -- ]

    -- Session metadata
    session_start TIMESTAMP NOT NULL,
    last_activity TIMESTAMP NOT NULL,
    event_count INTEGER DEFAULT 0,

    -- Computed features (for fast inference)
    features JSONB,
    -- Expected structure: {
    --   "hour_of_day": 14,
    --   "day_of_week": 3,
    --   "avg_time_between_events": 5.2,
    --   "session_duration_minutes": 15
    -- }

    -- TTL management
    expires_at TIMESTAMP NOT NULL,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(dataset_id, user_id, session_id)
);

CREATE INDEX idx_user_sessions_dataset ON user_sessions(dataset_id);
CREATE INDEX idx_user_sessions_tenant ON user_sessions(tenant_id);
CREATE INDEX idx_user_sessions_user ON user_sessions(dataset_id, user_id);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_activity ON user_sessions(last_activity DESC);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_datasets_updated_at BEFORE UPDATE ON datasets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_events_metadata_updated_at BEFORE UPDATE ON events_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_sessions_updated_at BEFORE UPDATE ON user_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE datasets IS 'Registry of event datasets with flexible schema configuration';
COMMENT ON COLUMN datasets.column_mapping IS 'Maps CSV columns to semantic roles (user, item, timestamp, etc.)';
COMMENT ON COLUMN datasets.session_config IS 'Configuration for session boundary detection';

COMMENT ON TABLE dataset_uploads IS 'History of all file uploads to datasets';
COMMENT ON COLUMN dataset_uploads.validation_errors IS 'Detailed validation errors for rejected rows';

COMMENT ON TABLE events_metadata IS 'Aggregated statistics per partition for fast queries';
COMMENT ON COLUMN events_metadata.stats IS 'Flexible statistics including distributions and top-K lists';

COMMENT ON TABLE user_sessions IS 'Active user session state for real-time recommendations';
COMMENT ON COLUMN user_sessions.recent_items IS 'Ordered sequence of recent items for inference';
COMMENT ON COLUMN user_sessions.features IS 'Pre-computed features to reduce inference latency';
