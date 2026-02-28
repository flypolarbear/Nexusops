# Logs Visual Test

## URL
`/logs`

## Viewport
- Width: 1920
- Height: 1080

## Prerequisites
- Backend API running on `http://localhost:8000`
- Frontend running on `http://localhost:5173`
- Log data available (or mock data)

---

## Screenshots

### Screenshot 1: Log Viewer
- **Action**: Navigate to `/logs` and wait for page to load
- **Wait for**: `networkidle`
- **Capture**: Full page screenshot

### Screenshot 2: Filtered Logs
- **Action**: Apply filters (e.g., ERROR level only)
- **Wait for**: Logs filtered
- **Capture**: Filtered view

### Screenshot 3: Log Detail
- **Action**: Click on a log entry to expand
- **Wait for**: Detail panel/modal
- **Capture**: Expanded view

---

## Assertions

### Aesthetics

#### A1: Log Display
- **Expected**: Log viewer has clean, readable format
- **Check**:
  - Monospace font for log content
  - Proper line spacing
  - Timestamp column visible
  - Log level column with color coding

#### A2: Syntax Highlighting
- **Expected**: Log content has syntax highlighting
- **Check**:
  - JSON logs formatted with colors
  - Stack traces highlighted
  - URLs clickable

#### A3: Color Coding
- **Expected**: Log levels have distinct colors
- **Check**:
  - ERROR: Red
  - WARN: Yellow/Orange
  - INFO: Blue/Green
  - DEBUG: Gray

### Interaction

#### I1: Filtering Controls
- **Expected**: Filter controls are accessible
- **Check**:
  - Level dropdown (ERROR, WARN, INFO, DEBUG)
  - Service selector
  - Time range picker
  - Search input

#### I2: Auto-Scroll
- **Expected**: Auto-scroll toggle for live logs
- **Check**:
  - Toggle button visible
  - Auto-scroll on by default (optional)
  - Scroll position indicator

#### I3: Copy Functionality
- **Expected**: Can copy log content
- **Check**:
  - Copy button per entry
  - Copy all visible logs
  - Copy selection

### Functionality

#### F1: Log Streaming
- **Expected**: Logs stream in real-time
- **Check**:
  - New logs appear automatically
  - Connection status indicator
  - Pause/resume functionality

#### F2: Log Search
- **Expected**: Search works across log content
- **Check**:
  - Search highlights matches
  - Navigate between matches
  - Search history

#### F3: Log Export
- **Expected**: Can export logs
- **Check**:
  - Export to file option
  - Format selection (JSON, TXT)
  - Date range for export

---

## Error States to Check

### E1: No Logs
- **Trigger**: No log data available
- **Expected**: Empty state
- **Check**:
  - "No logs available" message
  - Time range suggestion
  - Refresh button

### E2: Connection Error
- **Trigger**: WebSocket disconnection
- **Expected**: Connection error handling
- **Check**:
  - Error banner displayed
  - Reconnection attempt indicator
  - Manual reconnect button
