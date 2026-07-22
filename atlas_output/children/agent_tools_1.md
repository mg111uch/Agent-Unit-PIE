# 📂 agent_tools_1
Generated: 2026-07-21 18:31:40
Files: 10

---

F030│Llama_test.py│19
D: ●llama_cpp
---

F028│ask_gemini.py│178│⚡
S: Text/Video/Image Reasoning Script
D: ●argparse,dotenv,google,os,time,+1
F: get_last_call_time()→float
   ↳Called by: F028:enforce_rate_limit
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F028:enforce_rate_limit]
   S: Load last API call timestamp from state file.
F: save_last_call_time()
   ↳Called by: F028:enforce_rate_limit
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F028:enforce_rate_limit]
   S: Save current timestamp to state file.
F: enforce_rate_limit()
   ↳Called by: F028:main | Calls: F028:get_last_call_time,F028:save_last_call_time
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F028:main]
   S: Block if called before rate limit interval has passed.
F: main()
   ↳Calls: F028:enforce_rate_limit
---

F032│inference_api_hf.py│20
D: ●dotenv,huggingface_hub,os
---

F035│play_sound.py│11
D: ●datetime,playsound,time
---

F027│record_browser.py│54│⚡
D: ●os,pyppeteer,shutil,subprocess,time,+1
F: main()
---

F025│record_screen.py│90│⚡
S: Screen Recording Script
D: ●argparse,cv2,mss,numpy,time,+2
F: _signal_handler(signum,frame)
   S: Handle termination signals to properly save video.
F: record_screen(x,y,width,height,output_file,fps,duration)
---

F031│run_and_record.py│134│⚡
S: Wrapper script to run application and record video simultaneously.
D: ●argparse,os,re,subprocess,time,+2
F: extract_command_from_tools(tools_file_path,command_name)→str
   ↳Called by: F031:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F031:main]
   S: Extract command string from tools file by command name.
   S: The tools file format is:
   S: - **Command Name:** `actual command string`
   S: Returns the command string (without backticks).
F: run_app_command(app_cmd,app_done_event)
   S: Run the application command and signal when done.
F: record_video_before_app(record_cmd,init_delay,app_done_event)
   S: Start recording first, then wait for app to complete.
F: main()
   ↳Calls: F031:extract_command_from_tools
---

F029│run_process.py│177│⚡
S: Run Process with Duration Limit
D: ●argparse,os,subprocess,threading,time,+3
F: run_script_with_timeout(script_cmd,duration)
   ↳Called by: F029:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F029:main]
   S: Run a script command and terminate it after the specified duration.
   S: Args:
   S: script_cmd: Either a path to a .py file or a command string
   S: duration: Maximum duration in seconds before aborting
   S: Returns:
F: main()
   ↳Calls: F029:run_script_with_timeout
---

F026│screenshot_region.py│28│⚡
D: ●argparse,pyautogui
F: take_screenshot(x,y,width,height,output_file)
   S: Takes a screenshot of a specified region of the screen.
   S: Args:
   S: x (int): X coordinate of the top-left corner
   S: y (int): Y coordinate of the top-left corner
   S: width (int): Width of the screenshot region
---

F033│swapFiles.py│40│⚡
D: ●argparse,os,shutil
F: swap_files_in_directories(dir1,dir2)
   ↳Called by: F033:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F033:main]
   S: Swaps files with the same name and relative path between two directories.
F: main()
   ↳Calls: F033:swap_files_in_directories
---
