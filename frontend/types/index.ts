// User & Auth Types
export interface User {
  id: string;
  email: string;
  tenant_id: string;
  role: 'admin' | 'developer' | 'viewer';
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: User;
}

export interface Tenant {
  tenant_id: string;
  name: string;
  plan: 'starter' | 'pro' | 'enterprise';
  status: 'active' | 'suspended';
  created_at: string;
  settings: {
    default_model: string;
    embedding_dimension: number;
  };
}

// API Key Types
export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
  status: 'active' | 'revoked';
}

export interface CreateApiKeyRequest {
  name: string;
  permissions: string[];
}

export interface CreateApiKeyResponse {
  id: string;
  name: string;
  key: string;
  created_at: string;
}

// Usage & Analytics Types
export interface UsageMetrics {
  api_calls: number;
  recommendations_served: number;
  items_indexed: number;
  average_latency_ms: number;
}

export interface UsageData {
  period: {
    start: string;
    end: string;
  };
  metrics: UsageMetrics;
  quota: {
    api_calls_limit: number;
    api_calls_used: number;
    percentage_used: number;
  };
}

export interface UsageChartData {
  date: string;
  api_calls: number;
  recommendations: number;
}

// Data Upload Types
export interface UploadItemsRequest {
  items: Item[];
}

export interface Item {
  item_id: string;
  title: string;
  description: string;
  category: string;
  tags: string[];
  metadata?: Record<string, any>;
  created_at?: string;
}

export interface UploadItemsResponse {
  accepted: number;
  rejected: number;
  validation_errors: ValidationError[];
}

export interface ValidationError {
  item_id: string;
  error: string;
}

// Recommendation Types
export interface RecommendationRequest {
  user_id: string;
  count?: number;
  filters?: {
    categories?: string[];
    min_score?: number;
  };
  context?: {
    device_type?: string;
  };
}

export interface Recommendation {
  item_id: string;
  score: number;
}

export interface RecommendationResponse {
  recommendations: Recommendation[];
  metadata: {
    model_version: string;
    latency_ms: number;
  };
}

// Interaction Types
export interface Interaction {
  user_id: string;
  item_id: string;
  interaction_type: 'view' | 'click' | 'purchase' | 'like' | 'dislike';
  timestamp?: string;
  context?: Record<string, any>;
}

// Dashboard Types
export interface DashboardStats {
  total_api_calls: number;
  total_recommendations: number;
  total_items: number;
  avg_latency_ms: number;
  change_percentage: {
    api_calls: number;
    recommendations: number;
    items: number;
  };
}

export interface ActivityItem {
  id: string;
  type: 'upload' | 'api_call' | 'model_update' | 'api_key_created';
  message: string;
  timestamp: string;
  status: 'success' | 'error' | 'warning';
}

// Error Types
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
    request_id: string;
    timestamp: string;
  };
}
