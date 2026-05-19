# NetWatch - Windows Port Manager

## 1. Project Overview

- **Project Name**: NetWatch
- **Type**: Desktop GUI Application (Windows)
- **Core Functionality**: Visual port management tool that displays all running TCP/UDP ports with associated process information, and allows users to safely terminate processes
- **Target Users**: Windows developers, system administrators, DevOps engineers

## 2. UI/UX Specification

### Layout Structure

- **Single Window Application**
- **Header Area**: App title + search box + refresh button
- **Main Content**: Data table displaying port information with loading state
- **Window Size**: 1100x650 pixels (resizable, min 700x500)
- **Window Title**: "NetWatch - Port Manager"

### Visual Design

#### Color Palette
| Element | Color | Hex |
|---------|-------|-----|
| Background | Light Gray | #F5F7FA |
| Card Background | White | #FFFFFF |
| Primary Text | Dark Gray | #2D3748 |
| Secondary Text | Medium Gray | #718096 |
| Accent/Header | Deep Blue | #3182CE |
| Kill Button | Red | #DC2626 |
| Kill Button Hover | Transparent | - |
| Refresh Button | Gray | #718096 |
| Table Header | Light Blue Gray | #EDF2F7 |
| Table Row Hover | Very Light Blue | #EBF8FF |
| Table Border | Light Gray | #E2E8F0 |
| Selected Row | Light Blue | #90CDF4 |
| Selected Text | Dark | #1A202C |

#### Typography
- **Font Family**: Segoe UI (Windows native)
- **Header Title**: 20px, Semi-bold
- **Table Header**: 11px, Semi-bold
- **Table Body**: 11px, Regular
- **Button Text**: 11px, Medium/Bold
- **Status Bar**: 11px, Regular

#### Spacing System
- **Main Layout Padding**: 20px
- **Table Cell Padding**: 10px horizontal, 10px vertical
- **Button Padding**: variable

#### Visual Effects
- **No Focus Outline**: Focus indicator disabled on table
- **Row Selection**: Light blue background with dark text
- **No Context Menu**: Right-click disabled on table

### Components

#### Header Bar
- Left: App title "NetWatch 🌐"
- Center: Search box (250px width) for filtering ports
- Right: Refresh button with ↻ icon

#### Search Box
- Placeholder: "Search port, PID, or process name..."
- Border: 1px solid #E2E8F0, rounded 6px
- Focus state: border color #3182CE

#### Port Table
| Column | Resize Mode | Alignment |
|--------|-------------|-----------|
| Protocol | Fixed | Center |
| Local Address | ResizeToContents | Left |
| Port | Fixed | Center |
| PID | Fixed | Center |
| Process Name | Stretch | Left |
| Action | Fixed | Center |

#### Table Features
- Alternating row colors: White / #FAFBFC
- Hover state: #EBF8FF
- Selected state: #90CDF4
- No vertical header
- No grid lines
- Focus policy: NoFocus (no dotted outline)

#### Kill Button (per row)
- Text: "Kill"
- Style: Transparent background, red text (#DC2626), no border
- Disabled for whitelisted processes (gray text #A0AEC0)
- Tooltip on disabled: "System process - cannot be terminated"

#### Refresh Button (header)
- Text: "↻ Refresh"
- Color: Gray (#718096)

#### Loading State
- Shows "Loading ports..." label centered in table area
- Table is hidden during loading
- Loading label uses secondary text color (#718096)

#### Confirmation Dialog
- Modal dialog
- Title: "Confirm Kill"
- Message includes: Port, PID, Process Name
- Warning text: "This action cannot be undone."
- Buttons: "Cancel" (gray), "Kill" (red)

#### Status Bar (bottom)
- Shows: "Total: X ports | Last refreshed: HH:MM:SS"
- When searching: "Showing X of Y ports | Last refreshed: HH:MM:SS"
- Background: #EDF2F7

## 3. Functional Specification

### Core Features

#### F1: Port Scanning
- Use `netstat -ano` to get all TCP/UDP connections
- Batch load all process names using `tasklist /FO CSV /NH`
- Cache process names for performance
- Parse output to extract: Protocol, Local Address, Port, PID
- Match PIDs with process names from cache
- Display results in sorted table (by port number, then protocol)
- Exclude whitelisted system processes from display

#### F2: Process Termination
- Execute `taskkill /PID <pid> /F` for selected process
- Show success/failure notification (QMessageBox)
- Auto-refresh table after successful kill

#### F3: Whitelist Protection
Critical processes that CANNOT be killed (not displayed in list):
- System, smss.exe, csrss.exe, wininit.exe, services.exe
- lsass.exe, svchost.exe, winlogon.exe, explorer.exe
- dllhost.exe, rundll32.exe, Taskmgr, winmgmt.exe, spoolsv.exe
- And many other system processes

Whitelist check is case-insensitive substring match.

#### F4: Search/Filter
- Real-time filtering as user types
- Searches: port number, PID, process name, protocol, local address
- Shows "Showing X of Y ports" in status bar when filtered
- Clear search to show all ports

#### F5: Refresh
- Manual refresh button
- Auto-refresh on process kill
- Shows last refresh timestamp

#### F6: Async Loading
- Window displays immediately with loading indicator
- Port data loads in background thread (QThread)
- UI remains responsive during data loading

### User Interactions

1. **Launch App** → Window shows immediately with "Loading ports..." → Data loads in background → Table displays
2. **Type in Search** → Table filters in real-time
3. **Click Refresh** → Shows loading state → Re-scans and updates table
4. **Click Kill** → Shows confirmation dialog with port info
5. **Confirm Kill** → Terminates process, shows result, refreshes
6. **Cancel Kill** → Closes dialog, no action

### Data Flow

```
Launch → Show Window + Loading → Background Thread:
  netstat -ano → Parse → Batch tasklist → Match PIDs → Filter whitelist
  → Emit Ports → Display Table

Kill Request → Confirmation Dialog → taskkill /F → Result → Refresh
```

### Key Classes

1. **PortInfo** (dataclass)
   - protocol, local_addr, port, pid, process_name

2. **PortScanner**
   - _process_cache: dict
   - _load_all_processes(): batch load tasklist
   - _get_process_name(pid): from cache
   - get_all_ports(): returns List[PortInfo]

3. **PortScannerWorker** (QThread)
   - Runs get_all_ports() in background
   - finished signal emits List[PortInfo]

4. **ProcessKiller**
   - kill_process(pid): Tuple[bool, str]

5. **MainWindow** (QMainWindow)
   - _setup_ui(): builds interface
   - _apply_styles(): CSS styles
   - _start_loading(): starts background worker
   - _on_ports_loaded(): callback when data ready
   - _display_ports(): renders table
   - _on_search_changed(): filters ports
   - load_ports(): triggers reload

6. **ConfirmDialog** (QDialog)
   - Shows Port, PID, Process Name
   - Warning message

### Edge Cases

- PID not found: Show warning, refresh
- Access denied: Show error with admin hint
- Whitelisted process: Disable kill button, show tooltip
- Empty search results: Table shows filtered results
- Process terminates during load: Refresh handles it

## 4. Acceptance Criteria

### Visual Checkpoints
- [x] Window opens at 1100x650 with light gray background
- [x] Header shows title, search box, and refresh button
- [x] Loading indicator shows before data loads
- [x] Table has proper column headers
- [x] Rows show alternating colors
- [x] Kill buttons are red text, disabled for system processes
- [x] Status bar shows port count and last refresh time
- [x] Confirmation dialog shows Port/PID/Name
- [x] No focus outline on table cells
- [x] All text uses Segoe UI font

### Functional Checkpoints
- [x] Window displays immediately on launch
- [x] Port data loads in background (no UI freeze)
- [x] All TCP/UDP ports displayed (excluding system processes)
- [x] Port, PID, and process name are accurate
- [x] Kill button terminates the correct process
- [x] System processes are not shown in list
- [x] Refresh button updates the table
- [x] Search filters ports in real-time
- [x] Confirmation dialog prevents accidental kills
- [x] Success/failure notification appears after kill
