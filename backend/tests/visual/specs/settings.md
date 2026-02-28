# Settings Visual Test

## URL
`/settings`

## Viewport
- Width: 1920
- Height: 1080

## Prerequisites
- Backend API running on `http://localhost:8000`
- Frontend running on `http://localhost:5173`
- User with admin permissions (for full settings access)

---

## Screenshots

### Screenshot 1: Settings Overview
- **Action**: Navigate to `/settings` and wait for page to load
- **Wait for**: `networkidle`
- **Capture**: Full page screenshot

### Screenshot 2: AI Provider Section
- **Action**: Scroll to AI Provider configuration
- **Wait for**: Section visible
- **Capture**: Section screenshot

### Screenshot 3: Form Validation
- **Action**: Submit form with invalid data
- **Wait for**: Validation errors displayed
- **Capture**: Form with errors

---

## Assertions

### Aesthetics

#### A1: Section Organization
- **Expected**: Settings organized into clear sections
- **Check**:
  - Sections have clear headings
  - Related settings grouped together
  - Visual separation between sections

#### A2: Form Design
- **Expected**: Form elements are well designed
- **Check**:
  - Input fields have proper labels
  - Placeholder text is helpful
  - Required fields marked
  - Consistent input styling

#### A3: Help Text
- **Expected**: Help text/tooltips available for complex settings
- **Check**:
  - Tooltips on hover for confusing options
  - Description text below inputs
  - Links to documentation where appropriate

### Interaction

#### I1: Save Button
- **Expected**: Save functionality works correctly
- **Check**:
  - Save button visible at bottom
  - Disabled when no changes
  - Enabled when form modified
  - Loading state during save

#### I2: Cancel/Reset
- **Expected**: Cancel or reset option available
- **Check**:
  - Cancel button discards changes
  - Reset button restores defaults
  - Confirmation for unsaved changes

#### I3: Tab Navigation
- **Expected**: Tab navigation between sections works
- **Check**:
  - Tab labels are clear
  - Active tab highlighted
  - Tab content switches smoothly

### Functionality

#### F1: AI Provider Configuration
- **Expected**: AI provider settings are configurable
- **Check**:
  - Provider dropdown (OpenAI, Anthropic, etc.)
  - API key input field
  - Model selection
  - Test connection button

#### F2: Theme Settings
- **Expected**: Theme can be changed
- **Check**:
  - Light/Dark mode toggle
  - Theme applies immediately
  - Preference persisted

#### F3: Notification Settings
- **Expected**: Notification preferences configurable
- **Check**:
  - Email notifications toggle
  - Alert thresholds
  - Notification channels

---

## Error States to Check

### E1: Invalid API Key
- **Trigger**: Enter invalid API key and test connection
- **Expected**: Connection test fails gracefully
- **Check**:
  - Error message displayed
  - Form remains editable
  - Retry option available

### E2: Permission Denied
- **Trigger**: Non-admin user accesses admin settings
- **Expected**: Appropriate permission error
- **Check**:
  - Settings read-only or hidden
  - Permission message displayed
  - Contact admin suggestion
