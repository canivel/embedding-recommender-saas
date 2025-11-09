export interface ColumnMapping {
  user_column: string;
  item_column: string;
  timestamp_column: string;
  session_column?: string;
  target_column?: string;
}

export interface SessionConfig {
  auto_detect: boolean;
  timeout_minutes: number;
}

export interface Dataset {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  column_mapping: ColumnMapping;
  session_config: SessionConfig;
  upload_count: number;
  total_events: number;
  total_sessions: number;
  unique_users: number;
  unique_items: number;
  status: 'active' | 'archived' | 'processing';
  created_at: string;
  updated_at: string;
  last_upload_at?: string;
}

export interface DatasetCreate {
  name: string;
  description?: string;
  column_mapping: ColumnMapping;
  session_config?: SessionConfig;
}

export interface DatasetUpdate {
  name?: string;
  description?: string;
  column_mapping?: ColumnMapping;
  session_config?: SessionConfig;
  status?: 'active' | 'archived';
}

export interface DatasetUpload {
  id: string;
  dataset_id: string;
  filename: string;
  file_size_bytes?: number;
  row_count: number;
  accepted: number;
  rejected: number;
  validation_errors?: Array<{ error: string }>;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  uploaded_at: string;
  metadata?: {
    unique_users: number;
    unique_items: number;
    date_range: {
      start: string;
      end: string;
    };
    total_sessions: number;
  };
}

export interface EventRecord {
  user_id: string;
  item_id: string;
  timestamp: string;
  session_id?: string;
  target?: any;
  [key: string]: any;
}

export interface EventsQueryParams {
  limit?: number;
  offset?: number;
  user_id?: string;
  item_id?: string;
  start_date?: string;
  end_date?: string;
  session_id?: string;
}

export interface EventsQueryResponse {
  events: EventRecord[];
  total: number;
  limit: number;
  offset: number;
}

export interface DatasetStatistics {
  dataset_id: string;
  dataset_name: string;
  total_events: number;
  unique_users: number;
  unique_items: number;
  uploads: number;
  date_range: {
    start: string | null;
    end: string | null;
  };
}
