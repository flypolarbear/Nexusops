# Dashboard Visual Test

## URL
`/`

## Viewport
- Width: 1920
- Height: 1080

## Prerequisites
- Backend API running on `http://localhost:8000`
- Frontend running on `http://localhost:5173`
- User logged in (or login page visible)

---

## Screenshots

### Screenshot 1: Dashboard Overview
- **Action**: Navigate to `/` and wait for page to load
- **Wait for**: `networkidle` (no network activity for 500ms)
- **Capture**: Full page screenshot

### Screenshot 2: Mobile View
- **Action**: Resize viewport to 375x812 (iPhone)
- **Wait for**: Layout adjustment
- **Capture**: Full page screenshot

---

## Assertions

### Aesthetics

#### A1: Layout Balance
- **Expected**: Dashboard has a clean, professional layout with proper spacing
- **Check**:
  - Cards/sections are evenly distributed
  - Consistent padding and margins
  - No visual clutter or overlapping elements

#### A2: Color Scheme
- **Expected**: Colors are consistent with design system
- **Check**:
  - Primary color used correctly
  - Status colors (success/warning/error) are distinguishable
  - Text contrast meets WCAG AA standards

#### A3: Typography
- **Expected**: Fonts are readable and hierarchy is clear
- **Check**:
  - Headings are larger than body text
  - Font sizes are appropriate for content
  - No text overflow or truncation issues

### Interaction

#### I1: Navigation Sidebar
- **Expected**: Sidebar navigation is intuitive and accessible
- **Check**:
  - All menu items have icons and labels
  - Current page is highlighted
  - Hover states are visible

#### I2: Clickable Elements
- **Expected**: Buttons and links are clearly clickable
- **Check**:
  - Buttons have proper padding and cursor
  - Links are underlined or colored
  - Focus states are visible for keyboard navigation

### Functionality

#### F1: Statistics Cards
- **Expected**: Four stat cards displaying key metrics
- **Check**:
  - Cards show: Services, Clusters, Alerts, Health
  - Numbers are formatted correctly
  - Icons are displayed for each metric
  - Trend indicators if applicable

#### F2: Charts/Graphs
- **Expected**: Data visualizations are rendered correctly
- **Check**:
  - Charts load without errors
  - Axes are labeled
  - Legends are visible
  - Data points are accurate

#### F3: Recent Activity
- **Expected**: Recent activity section shows latest events
- **Check**:
  - Events are listed with timestamps
  - Event types are distinguishable
  - Links to details work

---

## Error States to Check

### E1: API Error
- **Trigger**: Stop backend API
- **Expected**: Error message displayed gracefully
- **Check**:
  - No broken images or missing data
  - User-friendly error message
  - Retry option available

### E2: Empty State
- **Trigger**: New user with no data
- **Expected**: Empty state with guidance
- **Check**:
  - Illustration or icon
  - Helpful message
  - Call-to-action if applicable
