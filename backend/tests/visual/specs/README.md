# Visual Test Specifications

This directory contains visual test specifications for NexusOps frontend pages.

## How OpenCode Executes These Tests

1. **Read spec file** - OpenCode reads the Markdown spec
2. **Start frontend** - Ensure `npm run dev` is running on `http://localhost:5173`
3. **Navigate to page** - Use `chrome-devtools` tools
4. **Capture screenshots** - Use `chrome-devtools_take_screenshot`
5. **Analyze with vision** - Use `zai-mcp-server_ui_to_artifact` or `zai-mcp-server_analyze_image`
6. **Report results** - Document pass/fail/warning with observations

## Test Categories

| Category | Description |
|----------|-------------|
| `aesthetics` | Visual design quality, spacing, colors, typography |
| `interaction` | UI behavior, clickable elements, hover states |
| `functionality` | Feature completeness, data display, errors |

## Available Specs

- [Dashboard](./dashboard.md) - Main dashboard overview
- [Agent Store](./agent-store.md) - Agent marketplace
- [Settings](./settings.md) - Application settings
- [Deployments](./deployments.md) - Deployment management
- [Logs](./logs.md) - Log viewer

## Spec Format

Each spec file follows this structure:

```markdown
# Page Name

## URL
/relative/path

## Viewport
- Width: 1920
- Height: 1080

## Screenshots
### Screenshot 1: [Name]
- Action: [what to do before capture]
- Wait for: [networkidle / selector / timeout]

## Assertions
### [Category] - [Description]
- Expected: [what should be visible/correct]
- Check: [specific things to verify]
```

## Running Tests

Ask OpenCode:

```
Run visual tests for [page name]
```

Or run all:

```
Run all visual tests
```
