# Writing Navigation Tests

This guide explains how to write navigation test files that can be executed by the `navigation.py` script.

## Overview

Navigation tests are written in Markdown format and consist of a sequence of commands that simulate user interactions (clicks, typing, pauses). These tests are used to automate UI testing by controlling the mouse and keyboard.

## File Format

Each command should be on its own line. Lines starting with `-` or `*` (Markdown list markers) are supported.

```
- command_type argument1 argument2
```

## Available Commands

### 1. run_conductor move

Move mouse to absolute screen coordinates without clicking.

**Syntax:**
```
run_conductor move <x> <y>
```

**Parameters:**
- `<x>` - X coordinate on screen
- `<y>` - Y coordinate on screen

**Example:**
```
run_conductor move 100 200
```

---

### 2. run_conductor click

Left click at absolute screen coordinates.

**Syntax:**
```
run_conductor click <x> <y>
```

**Parameters:**
- `<x>` - X coordinate of the click position
- `<y>` - Y coordinate of the click position

**Example:**
```
run_conductor click 192 1053
run_conductor click 80 300
```

---

### 3. run_conductor double_click

Double left click at absolute screen coordinates.

**Syntax:**
```
run_conductor double_click <x> <y>
```

**Parameters:**
- `<x>` - X coordinate of the click position
- `<y>` - Y coordinate of the click position

**Example:**
```
run_conductor double_click 500 300
```

---

### 4. run_conductor right_click

Right click at absolute screen coordinates (opens context menu).

**Syntax:**
```
run_conductor right_click <x> <y>
```

**Parameters:**
- `<x>` - X coordinate of the click position
- `<y>` - Y coordinate of the click position

**Example:**
```
run_conductor right_click 400 400
```

---

### 5. run_conductor click_and_hold

Click and hold the mouse button at absolute screen coordinates.

**Syntax:**
```
run_conductor click_and_hold <x> <y>
```

**Parameters:**
- `<x>` - X coordinate of the position
- `<y>` - Y coordinate of the position

**Example:**
```
run_conductor click_and_hold 100 200
```

---

### 6. run_conductor release

Release the mouse button (used after click_and_hold).

**Syntax:**
```
run_conductor release
```

**Example:**
```
run_conductor release
```

---

### 7. run_conductor drag

Click and drag from one position to another.

**Syntax:**
```
run_conductor drag <x1> <y1> <x2> <y2>
```

**Parameters:**
- `<x1>` - Starting X coordinate
- `<y1>` - Starting Y coordinate
- `<x2>` - Ending X coordinate
- `<y2>` - Ending Y coordinate

**Example:**
```
run_conductor drag 100 200 400 200
```

---

### 8. run_conductor scroll

Scroll up or down on the page.

**Syntax:**
```
run_conductor scroll <clicks>
```

**Parameters:**
- `<clicks>` - Number of clicks (positive = scroll up, negative = scroll down)

**Example:**
```
run_conductor scroll -5
run_conductor scroll 3
```

---

### 9. run_conductor position

Get the current mouse position. Outputs to console (useful for debugging).

**Syntax:**
```
run_conductor position
```

**Example:**
```
run_conductor position
```

---

### 10. run_conductor screen_size

Get the screen resolution. Outputs to console.

**Syntax:**
```
run_conductor screen_size
```

**Example:**
```
run_conductor screen_size
```

---

### 11. run_conductor is_on_screen

Check if given coordinates are within screen bounds.

**Syntax:**
```
run_conductor is_on_screen <x> <y>
```

**Parameters:**
- `<x>` - X coordinate to check
- `<y>` - Y coordinate to check

**Example:**
```
run_conductor is_on_screen 1920 1080
```

---

### 12. action_pause

Pauses execution for a specified number of seconds. Use this to wait for UI updates, page loads, or animations to complete.

**Syntax:**
```
action_pause <seconds>
```

**Parameters:**
- `<seconds>` - Number of seconds to wait (integer)

**Example:**
```
action_pause 5
action_pause 1
```

---

### 13. type_text

Types text using the keyboard. This uses pyautogui's `write()` function.

**Syntax:**
```
type_text "<message>"
```

or without quotes (for simple text):

```
type_text <message>
```

**Parameters:**
- `<message>` - The text to type

**Example:**
```
type_text "Automated message 101"
type_text Hello World
```

---

## Complete Example

Here's a complete test file that demonstrates a chat message workflow:

```markdown
# Navigation to test chat message

# Open chat panel
- run_conductor click 192 1053

# Wait for chat panel to open
- action_pause 3

# Select first conversation/contact
- run_conductor click 80 300

# Wait for conversation to load
- action_pause 3

# Click on message input field
- run_conductor click 90 975

# Wait for input field to focus
- action_pause 1

# Move cursor to message input area
- run_conductor move 510 975

# Wait for cursor position
- action_pause 1

# Type the message content
- type_text "Automated message 101"

# Wait for text to appear in input
- action_pause 1

# Click send button to submit message
- run_conductor click 605 975
```
---

## Finding Screen Coordinates

To find the correct coordinates for your clicks:

1. **Use a screenshot tool** - Take a screenshot and identify pixel coordinates
2. **Use developer tools** - Inspect elements in the browser
3. **Manual testing** - Add temporary logging to find click positions

### Tips for Finding Coordinates:

- **Account for window position** - Coordinates are absolute screen coordinates
- **Test incrementally** - Add one click at a time and verify position
- **Include pauses** - Always add `action_pause` after clicks to let UI update
- **Consider monitor resolution** - Coordinates may need adjustment for different screens

---

## Best Practices

1. **Always include pauses** - Add `action_pause` after clicks to allow UI to respond
2. **Test incrementally** - Write and test one action at a time
3. **Use descriptive comments** - Add `#` comments to explain what each step does
4. **Handle variable timing** - Increase pause duration for slow network or animations
5. **Verify coordinates** - Double-check click positions before running full tests
6. **Keep tests focused** - Each test should cover one specific user journey

---

## Troubleshooting

### "Warning: Unknown command"

- Make sure the command is not preceded by extra characters
- Check that the command format matches the syntax above

### Clicks not reaching correct elements

- Coordinates may be off due to window position
- Use a tool to verify exact screen coordinates
- Consider if the UI has changed (responsive design, different viewport)

### Text not being typed

- Make sure the text input field is focused before typing
- Add a click action to focus the input first
- Check that the text doesn't contain special characters that pyautogui might interpret as commands
