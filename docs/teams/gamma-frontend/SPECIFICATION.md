# Team Gamma: Customer-Facing Frontend

## Mission
Build an intuitive web dashboard for customers to manage their recommendation system, view analytics, upload data, and manage API keys.

## Technology Stack
- **Framework**: React 18+ with Next.js 14
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State Management**: Zustand or Redux Toolkit
- **Data Fetching**: React Query (TanStack Query)
- **Charts**: Recharts or Chart.js
- **Forms**: React Hook Form + Zod validation
- **Auth**: NextAuth.js
- **Testing**: Jest + React Testing Library
- **Hosting**: Vercel or Netlify

## Pages & Features

### 1. Authentication
- **Login** (`/login`)
- **Sign Up** (`/signup`)
- **Password Reset** (`/reset-password`)
- **OAuth** (Google, GitHub)

### 2. Dashboard (`/dashboard`)
- Overview cards (API calls, recommendations served, items indexed)
- Usage graph (last 30 days)
- Model performance metrics
- Recent activity feed
- Quick actions (Upload data, Test recommendations)

### 3. Data Management (`/data`)
- **Upload Items** tab
  - CSV upload interface with drag-and-drop
  - Field mapping tool
  - Validation feedback
  - Bulk upload history
- **Interactions** tab
  - View recent interactions
  - Upload interaction data
  - Data quality dashboard

### 4. API Keys (`/api-keys`)
- List of API keys with status
- Create new key dialog
- Revoke/regenerate keys
- Usage per key
- Permissions management

### 5. Recommendations Testing (`/test`)
- User ID input
- Live recommendation preview
- Score visualization
- Filters configuration
- Export results

### 6. Analytics (`/analytics`)
- Model performance over time
- Top recommended items
- User engagement metrics
- A/B test results
- Custom date range selector

### 7. Settings (`/settings`)
- Tenant profile
- Team members management
- Billing & subscription
- Model configuration
- Notification preferences

### 8. Documentation (`/docs`)
- Integration guides
- API reference
- Code samples (Python, JavaScript, cURL)
- FAQs

## Component Structure

```
src/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── dashboard/page.tsx
│   ├── data/page.tsx
│   ├── api-keys/page.tsx
│   ├── analytics/page.tsx
│   └── layout.tsx
├── components/
│   ├── ui/
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   ├── Table.tsx
│   │   └── Modal.tsx
│   ├── Dashboard/
│   │   ├── OverviewCard.tsx
│   │   ├── UsageChart.tsx
│   │   └── ActivityFeed.tsx
│   ├── Data/
│   │   ├── CSVUploader.tsx
│   │   ├── FieldMapper.tsx
│   │   └── ValidationErrors.tsx
│   └── Layout/
│       ├── Sidebar.tsx
│       ├── Header.tsx
│       └── Footer.tsx
├── lib/
│   ├── api/
│   │   ├── client.ts
│   │   ├── recommendations.ts
│   │   ├── data.ts
│   │   └── auth.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useRecommendations.ts
│   │   └── useUsageData.ts
│   └── utils/
│       ├── formatters.ts
│       └── validators.ts
└── styles/
    └── globals.css
```

## Key Components

### API Client

```typescript
// lib/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 10000,
});

// Add auth token to all requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Refresh token logic
      const refreshToken = localStorage.getItem('refresh_token');
      const { data } = await axios.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken,
      });
      localStorage.setItem('access_token', data.access_token);

      // Retry original request
      error.config.headers.Authorization = `Bearer ${data.access_token}`;
      return axios(error.config);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Usage Dashboard

```typescript
// components/Dashboard/UsageChart.tsx
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { getUsageData } from '@/lib/api/usage';

export function UsageChart() {
  const { data, isLoading } = useQuery({
    queryKey: ['usage', 'last-30-days'],
    queryFn: () => getUsageData({ days: 30 }),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">API Usage (Last 30 Days)</h3>
      <LineChart width={600} height={300} data={data?.metrics}>
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="api_calls" stroke="#8884d8" />
        <Line type="monotone" dataKey="recommendations" stroke="#82ca9d" />
      </LineChart>
    </div>
  );
}
```

### CSV Uploader

```typescript
// components/Data/CSVUploader.tsx
import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadItems } from '@/lib/api/data';

export function CSVUploader() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);

  const { getRootProps, getInputProps } = useDropzone({
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
    onDrop: async (files) => {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', files[0]);

      try {
        const response = await uploadItems(formData);
        setResult(response);
      } catch (error) {
        console.error('Upload failed:', error);
      } finally {
        setUploading(false);
      }
    },
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center cursor-pointer hover:border-blue-500"
      >
        <input {...getInputProps()} />
        <p>Drag and drop CSV file here, or click to select</p>
      </div>

      {uploading && <p className="mt-4">Uploading...</p>}

      {result && (
        <div className="mt-4 p-4 bg-green-50 rounded">
          <p className="text-green-800">
            ✓ Uploaded {result.accepted} items successfully
          </p>
          {result.rejected > 0 && (
            <p className="text-red-800">
              ✗ {result.rejected} items failed validation
            </p>
          )}
        </div>
      )}
    </div>
  );
}
```

## State Management

```typescript
// lib/store/auth.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      login: async (email, password) => {
        const response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        });
        const data = await response.json();
        set({ user: data.user, token: data.access_token });
      },
      logout: () => set({ user: null, token: null }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

## Responsive Design
- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Sidebar collapses to hamburger menu on mobile
- Tables scroll horizontally on small screens
- Charts adapt to viewport size

## Performance Optimizations
- Code splitting (Next.js automatic)
- Image optimization (next/image)
- Lazy loading for heavy components
- React Query caching (5 min stale time)
- Debounced search inputs
- Virtual scrolling for large lists

## Success Criteria
- First contentful paint < 1.5s
- Time to interactive < 3s
- Lighthouse score > 90
- Mobile responsive (all breakpoints)
- Accessibility score > 95 (WCAG 2.1 AA)
- Zero TypeScript errors

## Development Workflow

### Phase 1 (Weeks 1-2)
- [ ] Project setup (Next.js, TypeScript, TailwindCSS)
- [ ] Authentication flow
- [ ] Dashboard skeleton
- [ ] API client setup

### Phase 2 (Weeks 3-4)
- [ ] Data upload interface
- [ ] API key management
- [ ] Usage analytics charts
- [ ] Settings page

### Phase 3 (Weeks 5-6)
- [ ] Recommendations testing tool
- [ ] Advanced analytics
- [ ] Polish & UX improvements
- [ ] Mobile responsiveness

### Phase 4 (Weeks 7-8)
- [ ] Integration testing
- [ ] Performance optimization
- [ ] Accessibility audit
- [ ] Production deployment
