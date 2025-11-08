# Quick Start Guide

Get the frontend dashboard running in 5 minutes.

## Prerequisites

- Node.js 18+ installed
- Backend API running on http://localhost:8000

## Setup Steps

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env.local` file:

```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### 3. Start Development Server

```bash
npm run dev
```

### 4. Access the Dashboard

Open your browser to: **http://localhost:3000**

## First Steps

### Create an Account

1. Click "Create Account" on the login page
2. Fill in:
   - **Company Name**: Your company
   - **Email**: your@email.com
   - **Password**: (min 8 characters)
3. Click "Create Account"

### Upload Data

1. Navigate to **Data** page
2. Drag and drop a CSV file or click to browse
3. Required CSV columns:
   - `item_id` - Unique item identifier
   - `title` - Item name
   - `description` - Item description
   - `category` - Item category

Example CSV:
```csv
item_id,title,description,category
item_001,Wireless Mouse,Ergonomic wireless mouse,electronics
item_002,USB-C Cable,Fast charging cable,electronics
item_003,Laptop Stand,Adjustable laptop stand,accessories
```

### Create API Key

1. Go to **API Keys** page
2. Click "Create API Key"
3. Enter a name (e.g., "Production Key")
4. Click "Create Key"
5. **IMPORTANT**: Copy the key immediately (shown only once)

### Test Recommendations

1. Navigate to **Test** page
2. Enter a user ID (e.g., "user_123")
3. Set number of results (default: 10)
4. Click "Get Recommendations"

## Common Issues

### Cannot connect to backend

**Error**: Network error or 404

**Solution**:
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check environment variable
cat .env.local
```

### Port already in use

**Error**: Port 3000 is already in use

**Solution**:
```bash
# Use different port
npm run dev -- -p 3001
```

### Module not found

**Error**: Cannot find module

**Solution**:
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

- ✅ Explore the **Dashboard** for metrics overview
- ✅ Check **Analytics** for performance insights
- ✅ Review **Documentation** for API integration
- ✅ Configure **Settings** for your account

## Production Build

When ready to deploy:

```bash
# Build optimized production bundle
npm run build

# Test production build locally
npm run start
```

## Need Help?

- Read the full [README.md](./README.md)
- Check [Documentation](/docs) page in the app
- Backend API docs: http://localhost:8000/docs

---

Happy recommending! 🚀
