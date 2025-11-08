# Internal Back Office - Quick Start Guide

## Getting Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd backoffice
npm install
```

This will install all required dependencies including:
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Zustand (state management)
- Recharts (charting)
- Axios (HTTP client)

### Step 2: Start Development Server

```bash
npm run dev
```

The application will start on **http://localhost:3000**

### Step 3: Login with Demo Account

Navigate to http://localhost:3000/login

**Quick Login Options:**
- **Super Admin**: admin@acme.com / admin123
- **Support**: support@acme.com / support123
- **Developer**: dev@acme.com / dev123

Or enter credentials manually and click "Sign In"

## Available Pages

Once logged in, you'll have access to the following pages based on your role:

### Dashboard (`/dashboard`)
- System overview with key metrics
- API usage trends
- System health status
- Recent alerts and activity

### Tenants (`/tenants`)
- View all customer tenants
- Search and filter tenants
- Create new tenants
- Edit tenant settings
- Suspend/activate tenants
- View API usage and quotas

**Click a tenant name to see detailed view:**
- Tenant settings and configuration
- API key management
- Usage history
- Model training jobs
- Team members

### Audit Logs (`/audit-logs`)
- View all administrative actions
- Search by user, action, or resource
- Filter by action type
- Export logs to CSV
- Pagination for large datasets

### System Monitoring (`/monitoring`)
- Real-time service health
- Service status indicators
- Performance metrics (latency, throughput, errors)
- CPU and resource usage
- Uptime statistics
- Performance charts

### Support Dashboard (`/support`)
- Tenant health scorecards
- Identify critical issues
- Error rates and latency metrics
- Impersonate tenants for debugging
- Visual health analytics

## Key Features Walkthrough

### Tenant Management

1. **List View**
   - Search by tenant name or email
   - See API usage percentage
   - Quick actions: Edit or Suspend

2. **Create Tenant**
   - Click "New Tenant" button
   - Enter tenant name, email, and plan
   - Click "Create"

3. **Edit Tenant**
   - Click pencil icon on any tenant
   - Modify details
   - Click "Update"

4. **Tenant Details Page**
   - Click tenant name to view full details
   - Manage API keys
   - View usage charts
   - Trigger model training
   - Check team information

### Tenant Impersonation

Useful for debugging tenant issues:

1. Go to Support Dashboard (`/support`)
2. Find the tenant you want to debug
3. Click the "Investigate" button
4. Provide a reason for impersonation
5. Click "Start Impersonation"
6. A yellow banner will show you're impersonating the tenant
7. All your actions are logged for audit
8. Click "Exit Impersonation" to return

### API Key Management

On tenant detail page:

1. View all API keys in the "API Keys" section
2. **Rotate Key**: Click rotation icon to generate new key
3. **Revoke Key**: Click trash icon to revoke key
4. Keys show creation date and last used date

### Model Training

On tenant detail page:

1. Scroll to "Model Training" section
2. Click "Trigger Training" button
3. Select model type:
   - Matrix Factorization
   - Two Tower (default)
   - Graph Neural Network
4. Click "Start Training"
5. Monitor training progress

### Audit Log Export

On audit logs page:

1. Use search and filters to narrow down logs
2. Click "Export CSV" button
3. CSV file will download with all filtered logs
4. Import into spreadsheet or analysis tool

## Mock Data

The application uses mock data for development:

- **Tenants**: 2 sample tenants (Acme Corp, TechStart Inc)
- **Audit Logs**: Sample administrative actions
- **System Health**: Mock service statuses
- **Alerts**: Sample system alerts

To modify mock data, edit `lib/api-client.ts` in the `mockAPI` object.

## Role-Based Access Control

The app enforces RBAC on the frontend (real enforcement happens on backend):

### Super Admin
- Full access to all features
- Can manage all tenants
- Can suspend/activate tenants
- Can manage system-wide features

### Support Agent
- Can view and help tenants
- Can impersonate tenants for debugging
- Can trigger retraining
- Cannot delete or suspend tenants

### Developer
- Can view tenants (read-only)
- Can trigger training for testing
- Can view system health
- Cannot manage tenants

## Environment Variables

Key environment variables in `.env.local`:

```env
NEXT_PUBLIC_APP_URL=http://localhost:3000        # App URL
NEXT_PUBLIC_API_URL=http://localhost:8000        # Backend API
NEXT_PUBLIC_MOCK_MODE=true                       # Use mock data
NEXTAUTH_SECRET=dev-secret                       # Session secret
NEXTAUTH_URL=http://localhost:3000              # NextAuth URL
```

Change these when deploying to production.

## Development Commands

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Run production build
npm start

# Type check
npm run type-check

# Lint code
npm run lint
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance Tips

1. **Search Optimization**: Use specific search terms for faster results
2. **Pagination**: Large datasets are paginated for performance
3. **Filtering**: Use filters to reduce data loaded
4. **Caching**: React Query caches data (5 min stale time)

## Troubleshooting

### Port 3000 Already in Use
```bash
npm run dev -- -p 3001
```

### Build Fails
```bash
rm -rf .next node_modules
npm install
npm run build
```

### TypeScript Errors
```bash
npm run type-check
```

### Mock Data Not Loading
- Verify `.env.local` has `NEXT_PUBLIC_MOCK_MODE=true`
- Check browser console for errors
- Refresh the page

## Next Steps

1. **Explore the UI**: Try different pages and actions
2. **Check the Spec**: Read `/docs/teams/delta-backoffice/SPECIFICATION.md`
3. **Integrate with Backend**: Update `lib/api-client.ts` to use real API
4. **Customize**: Modify components and add new features
5. **Deploy**: Set up CI/CD and deploy to production

## API Integration

When integrating with the real backend:

1. Update `NEXT_PUBLIC_API_URL` in `.env.local`
2. Set `NEXT_PUBLIC_MOCK_MODE=false`
3. Implement authentication (OAuth, SAML, etc.)
4. Update API client methods to remove mock data

See `lib/api-client.ts` for API endpoint definitions.

## Support & Documentation

- **Specification**: `/docs/teams/delta-backoffice/SPECIFICATION.md`
- **API Contracts**: `/docs/api-contracts/API_CONTRACTS.md`
- **System Architecture**: `/docs/architecture/SYSTEM_OVERVIEW.md`
- **Main README**: `./README.md`

## Security Notes

- Never commit `.env.local` with real secrets
- Use environment variables for sensitive data
- Impersonation requires logging for compliance
- All actions should be audited (real app)
- Use HTTPS in production

## Common Tasks

### Adding a New Page
1. Create folder in `app/`
2. Create `page.tsx` file
3. Add route to sidebar in `components/Layout/Sidebar.tsx`
4. Check permissions with `usePermission()` hook

### Adding a New Component
1. Create in `components/ui/` or `components/Layout/`
2. Use TypeScript for type safety
3. Follow existing component patterns
4. Add Tailwind CSS classes for styling

### Integrating with Backend API
1. Add method to `apiClient` in `lib/api-client.ts`
2. Use in page component with error handling
3. Show notifications with `useNotification()`
4. Handle loading states

## Performance Metrics

The application targets:
- First Contentful Paint (FCP) < 1.5s
- Time to Interactive (TTI) < 3s
- Lighthouse score > 90
- Cumulative Layout Shift (CLS) < 0.1

## Need Help?

1. Check the README.md for detailed documentation
2. Review component code comments
3. Check the specification for feature details
4. Look at similar pages for implementation patterns
5. Check browser DevTools console for errors

Happy coding! 🚀
