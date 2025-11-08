# Internal Back Office - Admin Portal

This is the Internal Back Office application for the Embedding Recommender SaaS platform. It provides comprehensive admin tools for the support team to manage tenants, debug issues, monitor system health, and perform administrative operations.

## Features

### Phase 1: Foundation (Completed)

- **SSO Authentication** - Google Workspace mock integration with role-based access control
- **Tenant Management** - List, create, edit, and suspend/activate tenants
- **Audit Logs** - Searchable, filterable activity logs with CSV export
- **Support Dashboard** - Monitor tenant health scores, error rates, and latency
- **System Monitoring** - Real-time service health and performance metrics
- **Tenant Impersonation** - Debug tenants by assuming their identity (with audit logging)
- **Role-Based Access Control** - Super Admin, Support, Developer roles with fine-grained permissions

### Demo Accounts

Three demo accounts are available for testing different roles:

| Email | Password | Role |
|-------|----------|------|
| admin@acme.com | admin123 | Super Admin |
| support@acme.com | support123 | Support |
| dev@acme.com | dev123 | Developer |

## Technology Stack

- **Framework**: Next.js 14 with React 18
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: Axios + React Query
- **Forms**: React Hook Form + Zod
- **Charts**: Recharts
- **Icons**: Lucide React
- **Date Handling**: date-fns

## Project Structure

```
backoffice/
├── app/                          # Next.js app directory
│   ├── layout.tsx               # Root layout
│   ├── globals.css              # Global styles
│   ├── login/                   # Authentication page
│   ├── dashboard/               # Main dashboard
│   ├── tenants/                 # Tenant management
│   │   ├── page.tsx            # Tenant list
│   │   └── [id]/               # Tenant details
│   ├── audit-logs/              # Audit logs viewer
│   ├── monitoring/              # System monitoring
│   └── support/                 # Support dashboard
│
├── components/
│   ├── ui/                       # Reusable UI components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   ├── Table.tsx
│   │   ├── Modal.tsx
│   │   └── Badge.tsx
│   └── Layout/                   # Layout components
│       ├── Sidebar.tsx
│       ├── Header.tsx
│       └── MainLayout.tsx
│
├── lib/
│   ├── types.ts                 # TypeScript type definitions
│   ├── auth.ts                  # Authentication logic & RBAC
│   ├── api-client.ts            # API client with mock support
│   └── store.ts                 # Zustand stores (auth, UI, filters)
│
├── package.json                 # Dependencies
├── tsconfig.json                # TypeScript config
├── tailwind.config.js           # Tailwind configuration
├── next.config.js               # Next.js configuration
├── postcss.config.js            # PostCSS configuration
└── .env.local                   # Environment variables
```

## Setup & Installation

### Prerequisites

- Node.js 18+
- npm or yarn package manager

### Installation Steps

```bash
# Navigate to backoffice directory
cd backoffice

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

### Environment Variables

The `.env.local` file includes:

```env
# Application
NEXT_PUBLIC_APP_NAME=Backoffice Admin
NEXT_PUBLIC_APP_URL=http://localhost:3000

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# SSO Configuration
GOOGLE_CLIENT_ID=mock-client-id
GOOGLE_CLIENT_SECRET=mock-client-secret

# Session
NEXTAUTH_SECRET=your-secret-key-change-in-production
NEXTAUTH_URL=http://localhost:3000

# Mock Data
NEXT_PUBLIC_MOCK_MODE=true
```

## Usage

### Login

1. Navigate to `http://localhost:3000/login`
2. Choose one of the demo accounts or enter credentials manually
3. Click "Sign In" or use quick login buttons

### Key Features

#### Dashboard
- View system overview with key metrics
- Monitor API usage and system health
- See recent tenant activity
- Check active system alerts

#### Tenant Management
- Search and filter tenants
- Create new tenants
- Edit tenant details (name, plan, email)
- Suspend/activate tenants
- View API usage and quota
- Manage API keys (rotate, revoke)
- Trigger model training jobs

#### Audit Logs
- Search logs by user, action, or resource
- Filter by action type
- Export logs to CSV
- View detailed information about each action
- Pagination support for large datasets

#### Support Dashboard
- Monitor tenant health scores
- Identify critical issues
- View error rates and latency
- Impersonate tenants for debugging
- Visual health metrics and charts

#### System Monitoring
- Real-time service health status
- Latency and error rate charts
- CPU usage monitoring
- Throughput metrics
- Uptime statistics
- Service-level status indicators

### RBAC Permissions

The application enforces role-based access control:

**Super Admin** has access to all features:
- View and manage all tenants
- Create/edit/delete tenants
- Suspend/activate tenants
- Impersonate tenants
- View audit logs
- Manage system features
- Trigger model training

**Support Agent** can:
- View all tenants
- Edit tenant settings
- Impersonate tenants (for debugging)
- View audit logs
- Trigger model training
- View system health

**Developer** can:
- View tenants (read-only)
- View audit logs
- View system health
- Trigger model training (for testing)

## API Integration

The application is designed to work with a backend API that provides these endpoints:

```
POST   /admin/tenants                    - Create tenant
GET    /admin/tenants                    - List tenants
GET    /admin/tenants/{id}               - Get tenant details
PUT    /admin/tenants/{id}               - Update tenant
POST   /admin/tenants/{id}/suspend       - Suspend tenant
POST   /admin/tenants/{id}/activate      - Activate tenant
GET    /admin/audit-logs                 - Get audit logs
GET    /admin/audit-logs/export          - Export logs (CSV)
GET    /admin/health                     - System health status
GET    /admin/alerts                     - Get system alerts
POST   /admin/impersonate/{tenant_id}    - Start impersonation
POST   /admin/tenants/{id}/training      - Trigger model training
GET    /admin/tenants/{id}/training/jobs - Get training jobs
GET    /admin/dashboard/tenant-health    - Get tenant health scores
```

For development, the application uses mock data. See `lib/api-client.ts` for mock data structure.

## Development

### Build for Production

```bash
npm run build
npm start
```

### Type Checking

```bash
npm run type-check
```

### Code Quality

The project uses:
- TypeScript for type safety
- ESLint for code linting
- Tailwind CSS for consistent styling
- React best practices

## Security Considerations

- **No PII in Logs**: Sensitive data is masked
- **Audit Trail**: All admin actions are logged with user attribution
- **Session Management**: Tokens stored securely in localStorage
- **RBAC**: Fine-grained permissions enforced on frontend and backend
- **Impersonation Logging**: All impersonation sessions are tracked

## Performance Optimizations

- Next.js automatic code splitting
- React Query caching
- Lazy loading for heavy components
- Virtual scrolling for large lists
- Debounced search inputs
- CSS-in-JS optimization with Tailwind

## Accessibility

- WCAG 2.1 AA compliant
- Keyboard navigation support
- Screen reader friendly
- High contrast mode support
- Proper heading hierarchy

## Deployment

### Vercel (Recommended)

```bash
# Connect repository to Vercel
# Environment variables are set in Vercel dashboard
# Automatic deployments on push to main
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables for Production

- `NEXTAUTH_SECRET` - Strong random string for session encryption
- `NEXTAUTH_URL` - Production URL
- `NEXT_PUBLIC_API_URL` - Backend API URL
- OAuth credentials if using real SSO

## Monitoring & Logging

The application includes:
- Built-in error handling with user-friendly messages
- Structured logging for debugging
- Performance monitoring (Lighthouse scores >90)
- Error tracking (integrate with Sentry, DataDog, etc.)

## Future Enhancements (Phase 2-3)

- Data quality dashboards
- Feature flag management UI
- Advanced analytics
- Custom reporting
- Real Grafana dashboard integration
- Multi-language support
- Dark mode theme
- Advanced search with filters
- Batch operations
- Webhooks management

## Testing

```bash
# Component testing
npm run test

# E2E testing
npm run test:e2e

# Coverage report
npm run test:coverage
```

## Troubleshooting

### Port Already in Use

```bash
# Use different port
npm run dev -- -p 3001
```

### Build Errors

```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

### TypeScript Errors

```bash
# Type check
npm run type-check

# Fix issues in code and re-run
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run type checks and lint
4. Submit a pull request

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the specification: `/docs/teams/delta-backoffice/SPECIFICATION.md`
3. Contact the development team

## License

Proprietary - All rights reserved
