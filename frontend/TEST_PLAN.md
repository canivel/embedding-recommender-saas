# Frontend Test Plan

Comprehensive testing checklist for the Embedding Recommender SaaS frontend.

## Pre-Test Setup

- [ ] Backend API is running on http://localhost:8000
- [ ] Frontend dev server is running on http://localhost:3000
- [ ] `.env.local` is configured with correct API URL
- [ ] Browser developer tools are open (for debugging)

## 1. Authentication Tests

### Login Flow
- [ ] Navigate to http://localhost:3000 (should redirect to /login)
- [ ] Form validation works:
  - [ ] Empty email shows error
  - [ ] Invalid email format shows error
  - [ ] Short password shows error
- [ ] Login with valid credentials works
- [ ] Success redirects to /dashboard
- [ ] Auth token is stored in localStorage
- [ ] "Remember me" checkbox toggles
- [ ] "Forgot password" link is clickable

### Signup Flow
- [ ] Navigate to /signup
- [ ] Form validation works:
  - [ ] Company name required (min 2 chars)
  - [ ] Email validation
  - [ ] Password min 8 characters
  - [ ] Password confirmation matches
- [ ] Successful signup creates account
- [ ] Auto-login after signup
- [ ] Redirect to dashboard

### Logout
- [ ] Logout from user menu
- [ ] Redirect to /login
- [ ] Auth token cleared from localStorage
- [ ] Cannot access protected routes after logout

## 2. Dashboard Tests

### Overview Cards
- [ ] All 4 cards render:
  - [ ] API Calls card
  - [ ] Recommendations Served card
  - [ ] Items Indexed card
  - [ ] Avg Latency card
- [ ] Loading skeleton shows while fetching
- [ ] Numbers format correctly (with commas)
- [ ] Trend indicators show (up/down arrows)
- [ ] Percentage changes display

### Usage Chart
- [ ] Chart renders with data
- [ ] X-axis shows dates
- [ ] Y-axis shows counts
- [ ] Two lines visible (API calls, Recommendations)
- [ ] Tooltip shows on hover
- [ ] Legend is visible and correct

### Activity Feed
- [ ] Recent activities list displays
- [ ] Icons match activity types
- [ ] Timestamps show relative time ("2 hours ago")
- [ ] "View All" button is clickable
- [ ] Empty state shows if no activities

### Quick Actions
- [ ] All 4 action cards visible
- [ ] Clicking "Upload Data" navigates to /data
- [ ] Clicking "Create API Key" navigates to /api-keys
- [ ] Clicking "Test Recommendations" navigates to /test
- [ ] Clicking "View Docs" navigates to /docs

## 3. Data Management Tests

### CSV Upload
- [ ] Drag and drop zone visible
- [ ] Click to browse works
- [ ] File selection shows file info
- [ ] Upload button enabled when file selected
- [ ] Progress indicator during upload
- [ ] Success message with count of accepted items
- [ ] Error handling for invalid CSV
- [ ] Validation errors display correctly
- [ ] "Upload Another File" resets state

### Upload History
- [ ] Table shows previous uploads
- [ ] Columns display: Filename, Uploaded, Status, Accepted, Rejected
- [ ] Status badges color-coded (green/red/yellow)
- [ ] Relative timestamps ("3 days ago")
- [ ] Empty state if no history

### Interactions Tab
- [ ] Tab switch works
- [ ] Stats cards show totals
- [ ] Upload interactions section visible
- [ ] Recent interactions table (or empty state)

## 4. API Keys Tests

### List API Keys
- [ ] Table shows existing keys
- [ ] Columns: Name, Key Prefix, Status, Created, Last Used, Actions
- [ ] Active keys show green badge
- [ ] Revoked keys show red badge
- [ ] Empty state shows if no keys

### Create API Key
- [ ] "Create API Key" button opens modal
- [ ] Form validation works (name required, min 3 chars)
- [ ] Submit creates key
- [ ] Full key shown once in modal
- [ ] Copy button copies to clipboard
- [ ] "Copied!" feedback shows
- [ ] Modal closes on "Done"
- [ ] Table updates with new key

### Revoke API Key
- [ ] "Revoke" button on active keys
- [ ] Confirmation dialog appears
- [ ] Confirming revokes the key
- [ ] Status changes to "Revoked"
- [ ] "Revoke" button disappears

## 5. Analytics Tests

### Page Load
- [ ] Date range selector works (7d, 30d, 90d)
- [ ] Key metrics cards display
- [ ] All 4 charts render:
  - [ ] Performance Over Time (line chart)
  - [ ] Top Recommended Items (bar chart)
  - [ ] Interaction Distribution (pie chart)
  - [ ] User Engagement Score (bar chart)

### Charts Interaction
- [ ] Tooltips appear on hover
- [ ] Legends are clickable
- [ ] Charts responsive to window resize
- [ ] "Export" button is clickable

### Model Performance Metrics
- [ ] Three metric cards show: Precision, Recall, F1 Score
- [ ] Values display correctly
- [ ] Last updated timestamp shows

## 6. Recommendations Testing

### Input Parameters
- [ ] User ID input accepts text
- [ ] Count input validates (1-50)
- [ ] Category filter is optional
- [ ] "Get Recommendations" button:
  - [ ] Disabled when user ID empty
  - [ ] Shows loading state during request
  - [ ] Enabled after response

### Results Display
- [ ] Recommendations list shows
- [ ] Each item shows: rank, item ID, score
- [ ] Score bar visualization
- [ ] Latency displayed in header
- [ ] Empty state before first request
- [ ] Error message on failure

## 7. Settings Tests

### Tab Navigation
- [ ] All 4 tabs clickable: Profile, Company, Billing, Notifications
- [ ] Active tab highlighted
- [ ] Content changes on tab switch

### Profile Settings
- [ ] Form fields editable
- [ ] Email validation
- [ ] Timezone selector works
- [ ] Save button submits changes

### Company Settings
- [ ] Company name editable
- [ ] Model selector dropdown works
- [ ] Embedding dimension input (number)
- [ ] Save button updates settings
- [ ] Loading state during save

### Billing
- [ ] Current plan displays
- [ ] "Upgrade Plan" button visible
- [ ] Usage bars show correctly
- [ ] Percentages accurate

### Notifications
- [ ] Checkboxes toggle on/off
- [ ] All 4 notification types listed
- [ ] Save preferences button works

## 8. Documentation Tests

### Navigation
- [ ] Sidebar with 3 sections: Getting Started, API Reference, Examples
- [ ] Active section highlighted
- [ ] Content changes on navigation

### Getting Started
- [ ] Step-by-step guide readable
- [ ] Headings properly formatted
- [ ] Content is helpful

### API Reference
- [ ] All 3 endpoints documented:
  - [ ] POST /recommendations
  - [ ] POST /items
  - [ ] POST /interactions
- [ ] HTTP methods color-coded
- [ ] Request/response examples visible

### Code Examples
- [ ] Python example with syntax highlighting
- [ ] JavaScript example with syntax highlighting
- [ ] cURL example with syntax highlighting
- [ ] Copy buttons work
- [ ] "Copied!" feedback shows

## 9. Responsive Design Tests

### Mobile (375px)
- [ ] Sidebar becomes hamburger menu
- [ ] Charts scale appropriately
- [ ] Tables scroll horizontally
- [ ] Cards stack vertically
- [ ] Forms are usable
- [ ] Buttons are tappable (min 44px)

### Tablet (768px)
- [ ] Layout adapts appropriately
- [ ] Two-column grids work
- [ ] Sidebar still visible
- [ ] Charts render well

### Desktop (1280px+)
- [ ] Full multi-column layouts
- [ ] Optimal spacing
- [ ] All content visible without scrolling (header area)

## 10. Error Handling Tests

### Network Errors
- [ ] Backend offline shows error
- [ ] Timeout shows error message
- [ ] Retry mechanism works
- [ ] User-friendly error messages

### Authentication Errors
- [ ] 401 triggers token refresh
- [ ] Failed refresh redirects to login
- [ ] Invalid credentials show error

### Validation Errors
- [ ] Form errors display clearly
- [ ] Field-level error messages
- [ ] Red borders on invalid inputs

### Empty States
- [ ] All pages handle no data gracefully
- [ ] Helpful empty state messages
- [ ] Call-to-action buttons present

## 11. Performance Tests

### Page Load
- [ ] Initial load < 3 seconds
- [ ] First contentful paint < 1.5s
- [ ] Time to interactive < 3s
- [ ] No layout shifts

### Interactions
- [ ] Button clicks responsive (< 100ms)
- [ ] Form submissions feel instant
- [ ] Chart rendering smooth
- [ ] No jank on scroll

### Caching
- [ ] React Query caches data
- [ ] Repeated requests use cache
- [ ] Stale data refetches appropriately

## 12. Accessibility Tests

### Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Focus indicators visible
- [ ] Enter/Space activate buttons
- [ ] Escape closes modals

### Screen Reader
- [ ] Buttons have labels
- [ ] Images have alt text
- [ ] Forms have proper labels
- [ ] Status messages announced

### Color Contrast
- [ ] Text readable on backgrounds
- [ ] Links distinguishable
- [ ] Buttons have sufficient contrast

## 13. Browser Compatibility

Test in:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

## 14. Integration Tests

### Full User Journey
1. [ ] New user signs up
2. [ ] Completes onboarding
3. [ ] Uploads data CSV
4. [ ] Creates API key
5. [ ] Tests recommendations
6. [ ] Views analytics
7. [ ] Updates settings
8. [ ] Logs out and logs back in

### Data Persistence
- [ ] Auth persists after page reload
- [ ] Zustand state rehydrates
- [ ] Local storage works correctly

## Test Results

| Category | Pass | Fail | Notes |
|----------|------|------|-------|
| Authentication | ☐ | ☐ | |
| Dashboard | ☐ | ☐ | |
| Data Management | ☐ | ☐ | |
| API Keys | ☐ | ☐ | |
| Analytics | ☐ | ☐ | |
| Testing | ☐ | ☐ | |
| Settings | ☐ | ☐ | |
| Documentation | ☐ | ☐ | |
| Responsive | ☐ | ☐ | |
| Errors | ☐ | ☐ | |
| Performance | ☐ | ☐ | |
| Accessibility | ☐ | ☐ | |
| Browsers | ☐ | ☐ | |

## Known Issues

Document any bugs found during testing:

1.
2.
3.

## Notes

Additional observations or comments:

---

**Tested by**: _________________
**Date**: _________________
**Environment**: _________________
