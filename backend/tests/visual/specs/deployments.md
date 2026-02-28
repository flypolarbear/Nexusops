# Deployments Visual Test

## URL
`/deployments`

## Viewport
- Width: 1920
- Height: 1080

## Prerequisites
- Backend API running on `http://localhost:8000`
- Frontend running on `http://localhost:5173`
- Some deployments data available

---

## Screenshots

### Screenshot 1: Deployments List
- **Action**: Navigate to `/deployments` and wait for page to load
- **Wait for**: `networkidle`
- **Capture**: Full page screenshot

### Screenshot 2: Deployment Detail
- **Action**: Click on a deployment row to expand/view details
- **Wait for**: Detail panel/modal
- **Capture**: Expanded view

### Screenshot 3: Deploy Modal
- **Action**: Click "New Deployment" button
- **Wait for**: Deploy modal/form
- **Capture**: Modal screenshot

---

## Assertions

### Aesthetics

#### A1: Table Design
- **Expected**: Deployment table is clean and readable
- **Check**:
  - Columns are properly sized
  - Headers are distinguishable
  - Row hover effect
  - Alternating row colors (optional)

#### A2: Status Indicators
- **Expected**: Status badges are clear and color-coded
- **Check**:
  - Success: Green
  - Running: Blue
  - Failed: Red
  - Pending: Yellow/Orange
  - Icons accompany status text

#### A3: Action Buttons
- **Expected**: Action buttons are visible and accessible
- **Check**:
  - Buttons for common actions (view, edit, delete)
  - Icons + text or icon-only with tooltips
  - Destructive actions styled differently

### Interaction

#### I1: Sorting
- **Expected**: Table columns are sortable
- **Check**:
  - Click header to sort
  - Sort indicator (arrow) visible
  - Toggle ascending/descending

#### I2: Filtering
- **Expected**: Filter options available
- **Check**:
  - Filter by status dropdown
  - Search by name input
  - Date range filter (optional)

#### I3: Pagination
- **Expected**: Pagination for large datasets
- **Check**:
  - Page size selector
  - Page numbers
  - Total count displayed

### Functionality

#### F1: Deployment List
- **Expected**: Deployments displayed with key information
- **Check**:
  - Service name
  - Version
  - Status
  - Last updated timestamp
  - Environment/namespace

#### F2: Deploy Flow
- **Expected**: New deployment can be created
- **Check**:
  - Form with required fields
  - Service selection
  - Version input
  - Environment selection
  - Confirmation before deploy

#### F3: Deployment Logs
- **Expected**: Can view deployment logs
- **Check**:
  - Logs accessible from detail view
  - Real-time log streaming
  - Log level filtering

---

## Error States to Check

### E1: No Deployments
- **Trigger**: No deployment history
- **Expected**: Empty state
- **Check**:
  - "No deployments" message
  - Illustration
  - "Create first deployment" CTA

### E2: Failed Deployment
- **Trigger**: View failed deployment details
- **Expected**: Error information displayed
- **Check**:
  - Error message/reason
  - Logs accessible
  - Retry option
