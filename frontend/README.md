# Embedding Recommender SaaS - Frontend Dashboard

A modern, production-ready customer-facing dashboard built with Next.js 14, TypeScript, and TailwindCSS for managing AI-powered recommendations.

## Features

- **Authentication**: Secure login/signup with JWT tokens
- **Dashboard**: Real-time metrics, usage charts, and activity feed
- **Data Management**: CSV upload with validation and drag-and-drop
- **API Key Management**: Create, view, and revoke API keys
- **Analytics**: Performance metrics, charts, and insights
- **Testing Interface**: Live recommendation testing tool
- **Settings**: Account and company configuration
- **Documentation**: Integration guides and code examples
- **Responsive Design**: Mobile, tablet, and desktop support

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Forms**: React Hook Form + Zod validation
- **Charts**: Recharts
- **File Upload**: React Dropzone
- **Icons**: Lucide React

## Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running at http://localhost:8000

## Installation

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env.local
   ```

   Edit `.env.local` and set:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser**:
   Navigate to http://localhost:3000

## Project Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Authentication routes
│   │   ├── login/
│   │   └── signup/
│   ├── (dashboard)/              # Dashboard routes
│   │   ├── dashboard/            # Overview page
│   │   ├── data/                 # Data management
│   │   ├── api-keys/             # API key management
│   │   ├── analytics/            # Analytics & metrics
│   │   ├── test/                 # Recommendations testing
│   │   ├── settings/             # Settings page
│   │   ├── docs/                 # Documentation
│   │   └── layout.tsx            # Dashboard layout
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Home page (redirects)
│   └── globals.css               # Global styles
│
├── components/                   # React components
│   ├── ui/                       # Reusable UI components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   ├── Table.tsx
│   │   ├── Loading.tsx
│   │   ├── ErrorBoundary.tsx
│   │   └── EmptyState.tsx
│   ├── Layout/                   # Layout components
│   │   ├── Sidebar.tsx
│   │   └── Header.tsx
│   ├── Dashboard/                # Dashboard components
│   │   ├── OverviewCards.tsx
│   │   ├── UsageChart.tsx
│   │   ├── ActivityFeed.tsx
│   │   └── QuickActions.tsx
│   ├── Data/                     # Data management components
│   │   ├── CSVUploader.tsx
│   │   ├── UploadHistory.tsx
│   │   └── InteractionsTab.tsx
│   └── providers/                # Context providers
│       └── QueryProvider.tsx
│
├── lib/                          # Utilities and logic
│   ├── api/                      # API client
│   │   ├── client.ts             # Axios instance
│   │   ├── auth.ts               # Authentication
│   │   ├── dashboard.ts          # Dashboard data
│   │   ├── data.ts               # Data upload
│   │   ├── api-keys.ts           # API keys
│   │   ├── tenant.ts             # Tenant info
│   │   ├── recommendations.ts    # Recommendations
│   │   └── analytics.ts          # Analytics
│   ├── store/                    # Zustand stores
│   │   └── auth.ts               # Auth store
│   ├── hooks/                    # Custom React hooks
│   │   └── useAuth.ts
│   └── utils.ts                  # Utility functions
│
├── types/                        # TypeScript types
│   └── index.ts                  # Type definitions
│
├── .env.example                  # Environment template
├── next.config.mjs               # Next.js configuration
├── tailwind.config.ts            # Tailwind configuration
├── tsconfig.json                 # TypeScript configuration
└── package.json                  # Dependencies
```

## Pages Overview

### Authentication

- **Login** (`/login`): User authentication with email/password
- **Signup** (`/signup`): New account registration

### Dashboard Routes

All dashboard routes require authentication:

- **Dashboard** (`/dashboard`): Overview with metrics, charts, and quick actions
- **Data** (`/data`): Upload CSV files, manage product catalog
- **API Keys** (`/api-keys`): Create and manage API keys
- **Analytics** (`/analytics`): Performance charts and metrics
- **Test** (`/test`): Live recommendation testing interface
- **Settings** (`/settings`): Account and company settings
- **Docs** (`/docs`): API documentation and code examples

## API Integration

The frontend connects to the Backend API at `http://localhost:8000` (configurable via `NEXT_PUBLIC_API_URL`).

### API Client Features

- **Automatic token refresh**: Handles 401 errors and refreshes JWT tokens
- **Request interceptors**: Adds auth token to all requests
- **Error handling**: Standardized error messages
- **Type safety**: Full TypeScript support

### Example Usage

```typescript
import { getRecommendations } from '@/lib/api/recommendations';

const recommendations = await getRecommendations({
  user_id: 'user_123',
  count: 10,
  filters: { categories: ['electronics'] }
});
```

## State Management

### Zustand Store (Auth)

```typescript
import { useAuthStore } from '@/lib/store/auth';

function MyComponent() {
  const { user, login, logout } = useAuthStore();
  // ...
}
```

### React Query (Data Fetching)

```typescript
import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from '@/lib/api/dashboard';

function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
  });
  // ...
}
```

## Available Scripts

```bash
# Development
npm run dev          # Start dev server (port 3000)

# Production
npm run build        # Build for production
npm run start        # Start production server

# Code Quality
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NODE_ENV` | Environment | `development` |

## Styling

### TailwindCSS

Custom theme configuration in `tailwind.config.ts`:

- Color palette: Blue (primary), Purple (secondary), Green (success), Red (error)
- Custom spacing, shadows, and animations
- Responsive breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)

### Component Patterns

```typescript
// Button variants
<Button variant="primary">Primary</Button>
<Button variant="outline">Outline</Button>

// Card component
<Card>
  <h3>Title</h3>
  <p>Content</p>
</Card>

// Loading states
<Loading size="lg" />
```

## Testing

Test your implementation:

1. **Authentication Flow**:
   - Visit http://localhost:3000
   - Create an account or login
   - Verify redirect to dashboard

2. **Dashboard Features**:
   - Check overview cards render
   - Verify charts display data
   - Test quick actions

3. **Data Upload**:
   - Navigate to Data page
   - Upload a CSV file
   - Verify validation and success messages

4. **API Keys**:
   - Create a new API key
   - Copy the key (shown once)
   - Test revoke functionality

5. **Recommendations Testing**:
   - Go to Test page
   - Enter a user ID
   - Verify recommendations display

## Troubleshooting

### Cannot connect to backend

- Ensure Backend API is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify CORS is enabled on backend

### Authentication issues

- Clear browser localStorage
- Check JWT token expiration
- Verify refresh token is valid

### Build errors

```bash
# Clear cache and reinstall
rm -rf .next node_modules
npm install
npm run build
```

### Type errors

```bash
# Run type checking
npm run type-check
```

## Performance

- **Code Splitting**: Automatic via Next.js
- **Image Optimization**: Using `next/image`
- **Lazy Loading**: Heavy components loaded on demand
- **React Query Caching**: 5-minute stale time
- **Debounced Inputs**: Search and filter operations

## Accessibility

- Semantic HTML
- ARIA labels on interactive elements
- Keyboard navigation support
- Focus management
- Screen reader friendly

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
```

### Docker

```bash
# Build Docker image
docker build -t embedding-frontend .

# Run container
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://api:8000 embedding-frontend
```

### Other Platforms

The app can be deployed to any platform supporting Node.js:
- Netlify
- Railway
- Render
- AWS Amplify

## Production Considerations

1. **Environment Variables**: Set production API URL
2. **Analytics**: Add tracking (Google Analytics, Mixpanel)
3. **Error Monitoring**: Integrate Sentry or similar
4. **CDN**: Serve static assets via CDN
5. **Security**: Enable CSP headers, HTTPS only

## Contributing

When adding new features:

1. Follow TypeScript strict mode
2. Use existing UI components
3. Add proper error handling
4. Include loading states
5. Ensure responsive design
6. Update this README

## License

Proprietary - All rights reserved

## Support

For issues or questions:
- Email: support@example.com
- Docs: /docs page in the app
- API Reference: http://localhost:8000/docs

---

Built with ❤️ using Next.js and TypeScript
