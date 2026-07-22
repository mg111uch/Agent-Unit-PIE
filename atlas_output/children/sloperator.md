# 📂 sloperator
Generated: 2026-07-21 18:31:40
Files: 4

---

F024│conductor.py│213│⚡
S: Conductor - Programmable Mouse Controller
D: ●argparse,pyautogui,sys
F: cmd_move(x,y)→None
   ↳Called by: F024:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F024:main]
   S: Move mouse to absolute position.
F: cmd_click(x,y,clicks)→None
   ↳Called by: F024:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F024:main]
   S: Click at absolute position.
F: cmd_double_click(x,y)→None
   ↳Called by: F024:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F024:main]
   S: Double click at absolute position.
F: cmd_right_click(x,y)→None
   ↳Called by: F024:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F024:main]
   S: Right click at absolute position.
F: cmd_click_and_hold(x,y)→None
   ↳Called by: F024:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F024:main]
   S: Click and hold at absolute position.
F: cmd_release()→None
   ↳Called by: F024:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F024:main]
   S: Release mouse button.
F: cmd_drag(x1,y1,x2,y2,duration)→None
   ↳Called by: F024:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F024:main]
   S: Drag from (x1, y1) to (x2, y2).
F: cmd_scroll(clicks)→None
   ↳Called by: F024:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F024:main]
   S: Scroll up (positive) or down (negative).
F: cmd_position()→None
   ↳Called by: F024:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F024:main]
   S: Get current mouse position.
F: cmd_screen_size()→None
   ↳Called by: F024:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F024:main]
   S: Get screen resolution.
F: cmd_is_on_screen(x,y)→None
   ↳Called by: F024:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F024:main]
   S: Check if coordinates are on screen.
F: main()
   ↳Calls: F024:cmd_click_and_hold,F024:cmd_click,F024:cmd_scroll
   S: Main entry point for conductor.
---

F022│navigation.py│81│⚡
S: Navigation module for AI Agent.
D: ●argparse,os,subprocess,sys,time,+1
F: run_conductor(command)→subprocess.CompletedProcess
   ↳Called by: F021:click,F023:move_mouse,F021:move_mouse
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F021:click],[F023:move_mouse],[F021:move_mouse]
   S: Run conductor.py with given command and arguments.
F: type_text(text)→None
   ↳Called by: F023:quick_post,F022:run_test_sequence
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F023:quick_post],[F022:run_test_sequence]
   S: Type text using pyautogui.
F: action_pause(seconds)
   ↳Called by: F022:run_test_sequence
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F022:run_test_sequence]
F: run_test_sequence(md_file_path)→None
   ↳Calls: F021:type_text,F022:run_conductor,F022:type_text
   S: Read and execute commands sequentially from a markdown test file.
---

F023│post_composer.py│181│⚡
S: Post on X Composer - AI-Powered Automated Post Generator and Quick Post using Conductor
D: ●google,os,random,subprocess,time,+4
F: run_conductor(command)→subprocess.CompletedProcess
   ↳Called by: F021:click,F023:move_mouse,F021:move_mouse
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F021:click],[F023:move_mouse],[F021:move_mouse]
   S: Run conductor.py with given command and arguments.
F: move_mouse(x,y)→None
   ↳Called by: F023:quick_post,F021:quick_post | Calls: F023:run_conductor,F021:run_conductor,F022:run_conductor
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F023:quick_post],[F021:quick_post]
   S: Move mouse to position.
F: click(x,y,clicks)→None
   ↳Called by: F023:quick_post,F021:quick_post | Calls: F023:run_conductor,F021:run_conductor,F022:run_conductor
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F023:quick_post],[F021:quick_post]
   S: Click at position.
F: type_text(text)→None
   ↳Called by: F023:quick_post,F022:run_test_sequence
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F023:quick_post],[F022:run_test_sequence]
   S: Type text using pyautogui.
F: quick_post(message)→bool
   ↳Called by: F023:main,F021:main | Calls: F021:click,F023:move_mouse,F023:click
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F023:main],[F021:main]
   S: Quick post - assumes X is already open and user is logged in.
F: get_random_wait_time()→float
   ↳Called by: F023:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F023:main]
   S: Get random wait time in hours between WAIT_MIN_HOURS and WAIT_MAX_HOURS.
F: get_prompt()→str
   ↳Called by: F023:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F023:main]
   S: Get a prompt to generate content from.
F: generate_content(prompt)→str
   ↳Called by: F023:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F023:main]
   S: Generate content using Gemini AI.
F: log(message)→None
   ↳Called by: F023:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F023:main]
   S: Log message with timestamp.
F: main()
   ↳Calls: F023:get_prompt,F023:generate_content,F023:log
   S: Main loop - runs indefinitely.
---

F021│post_on_X.py│87│⚡
S: Post on X (Twitter) - Quick Post using Conductor
D: ●os,pyautogui,subprocess,sys,time
F: run_conductor(command)→subprocess.CompletedProcess
   ↳Called by: F021:click,F023:move_mouse,F021:move_mouse
   ↳Impact: 🔴HIGH (5 dependents) | Breaks: [F021:click],[F023:move_mouse],[F021:move_mouse]
   S: Run conductor.py with given command and arguments.
F: move_mouse(x,y)→None
   ↳Called by: F023:quick_post,F021:quick_post | Calls: F023:run_conductor,F021:run_conductor,F022:run_conductor
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F023:quick_post],[F021:quick_post]
   S: Move mouse to position.
F: click(x,y,clicks)→None
   ↳Called by: F023:quick_post,F021:quick_post | Calls: F023:run_conductor,F021:run_conductor,F022:run_conductor
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F023:quick_post],[F021:quick_post]
   S: Click at position.
F: type_text(text)→None
   ↳Called by: F023:quick_post,F022:run_test_sequence
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F023:quick_post],[F022:run_test_sequence]
   S: Type text using pyautogui.
F: quick_post(message)→bool
   ↳Called by: F023:main,F021:main | Calls: F021:click,F023:move_mouse,F023:click
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F023:main],[F021:main]
   S: Quick post - assumes X is already open and user is logged in.
F: main()
   ↳Calls: F023:quick_post,F021:quick_post
   S: Main entry point.
---
