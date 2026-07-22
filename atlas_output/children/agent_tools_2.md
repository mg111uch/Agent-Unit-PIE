# 📂 agent_tools_2
Generated: 2026-07-21 18:31:40
Files: 3

---

F037│encrypt_env.py│64│⚡
S: Encrypt .env placeholders into .env.enc using a password.
D: ●__future__,base64,cryptography,getpass,os,+2
F: derive_key(password,salt)→bytes
   ↳Called by: F037:encrypt
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F037:encrypt]
F: encrypt(secrets,password)→bytes
   ↳Called by: F037:main | Calls: F037:derive_key
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F037:main]
F: parse_env(path)→Any
   ↳Called by: F037:main
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F037:main]
F: main()→None
   ↳Calls: F037:parse_env,F037:encrypt
---

F038│gemini_doc_clean.py│65│⚡
S: Strip JavaScript/REST sections or list/extract headings from gemini_doc.md.
D: ●os,re,sys
F: _read()→str
   ↳Called by: F038:clean,F038:list_headings,F038:extract
   ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F038:clean],[F038:list_headings],[F038:extract]
F: _write(text)→None
   ↳Called by: F038:clean,F038:extract
   ↳Impact: 🟡MEDIUM (2 dependents) | Breaks: [F038:clean],[F038:extract]
F: clean()→None
   ↳Called by: F038:main | Calls: F038:_read,F038:_write
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F038:main]
F: list_headings(level)→None
   ↳Called by: F038:main | Calls: F038:_read
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F038:main]
F: extract(heading)→None
   ↳Called by: F038:main | Calls: F038:_read,F038:_write
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F038:main]
F: main()→None
   ↳Calls: F038:list_headings,F038:clean,F100:extract
---

F036│screenRecord.py│118
D: ●cv2,numpy,os
---
