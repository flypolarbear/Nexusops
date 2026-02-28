# Agent Store Visual Test

## URL
`/agents`

## Viewport
- Width: 1920
- Height: 1080

## Prerequisites
- Backend API running on `http://localhost:8000`
- Frontend running on `http://localhost:5173`
- Agent data available in store

---

## Screenshots

### Screenshot 1: Agent Store Overview
- **Action**: Navigate to `/agents` and wait for page to load
- **Wait for**: `networkidle`
- **Capture**: Full page screenshot

### Screenshot 2: Agent Card Hover
- **Action**: Hover over first agent card
- **Wait for**: Hover state animation
- **Capture**: Viewport screenshot

### Screenshot 3: Agent Detail Modal
- **Action**: Click "View Details" on an agent card
- **Wait for**: Modal to open
- **Capture**: Modal screenshot

---

## Assertions

### Aesthetics

#### A1: Agent Card Design
- **Expected**: Agent cards have consistent, visually appealing design
- **Check**:
  - Cards have uniform size and spacing
  - Agent icons are clear and relevant
  - Status badges are visible
  - Shadow/elevation is consistent

#### A2: Color Coding
- **Expected**: Status and category colors are meaningful
- **Check**:
  - Installed vs available agents differentiated
  - Category tags have distinct colors
  - Status indicators (active/inactive) are clear

#### A3: Grid Layout
- **Expected**: Agent cards arranged in responsive grid
- **Check**:
  - Cards align properly in rows
  - Responsive breakpoints work
  - No orphan cards on edges

### Interaction

#### I1: Install Button
- **Expected**: Install button is accessible and functional
- **Check**:
  - Button is visible on each card
  - Hover state changes appearance
  - Click triggers install action
  - Loading state shown during install

#### I2: Search/Filter
- **Expected**: Search and filter functionality works
- **Check**:
  - Search input is visible
  - Filter dropdowns work
  - Results update in real-time
  - Clear filters option available

#### I3: Pagination
- **Expected**: Pagination works if many agents
- **Check**:
  - Page numbers visible
  - Next/prev buttons work
  - Current page highlighted

### Functionality

#### F1: Agent List Complete
- **Expected**: All built-in agents displayed
- **Check**:
  - Kubernetes Agent present
  - DNS Agent present
  - Logs Agent present
  - Cost Agent present
  - Deploy Agent present
  - Chat Agent present

#### F2: Agent Details
- **Expected**: Agent details modal shows complete info
- **Check**:
  - Description is accurate
  - Capabilities listed
  - Version shown
  - Author/maintainer info

#### F3: Install Flow
- **Expected**: Install flow works end-to-end
- **Check**:
  - Click install shows confirmation
  - Progress indicator during install
  - Success message on completion
  - Agent status updates to "installed"

---

## Error States to Check

### E1: No Agents Available
- **Trigger**: Empty agent store
- **Expected**: Empty state message
- **Check**:
  - Friendly illustration
  - "No agents available" message
  - Refresh button

### E2: Install Failed
- **Trigger**: Simulate install failure
- **Expected**: Error handling
- **Check**:
  - Error message displayed
  - Retry option available
  - Agent remains in "available" state
