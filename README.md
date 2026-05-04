# 🧠 Agent_Unit_PIE

**Pattern Intelligence Engine (PIE)**

Agent_Unit_PIE is a minimal, extensible AI agent built using the Gemini API.
It is designed to **analyze data, execute code, and persist structured knowledge** using markdown files.

---

## 🚀 Features

* 🔁 Multi-step reasoning loop (tool-driven)
* 🛠️ Tool execution (filesystem + shell)
* 🧠 Persistent memory via `.md` files
* 🧾 Structured knowledge extraction
* ⚙️ Safe file editing (`write_to_file`)
* 📂 Workspace sandboxing

---

## 🧩 Core Concept

This agent is not just a chatbot. It is a **Pattern Intelligence Engine**:

> It observes data → extracts patterns → stores them → reuses them.

All knowledge is stored as structured markdown inside:

```bash
/workspace/knowledge/
```

---

## ⚙️ Setup

### 1. Install dependencies

```bash
pip install google-genai python-dotenv
```

### 2. Set API key

Create `.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

---

## ▶️ Run the Agent

```bash
python agent.py
```

Then interact:

```bash
>> analyze files in workspace
>> build summary of project
>> create pattern notes
```

---

## 🛠️ Available Tools

### 1. `read_file`

Read contents of a file.

### 2. `list_files`

List directory contents.

### 3. `execute_command`

Run shell commands (restricted recommended).

### 4. `write_to_file`

Create and modify files safely.

#### Modes:

* `create` – new file
* `overwrite` – replace file
* `append` – add content
* `patch` – find & replace text

---

## 🧠 Agent Loop

```text
User Input
   ↓
LLM (decides action)
   ↓
Tool Execution
   ↓
Result fed back to LLM
   ↓
Repeat until final answer
```

---

## 📌 Design Principles

* **Tool-first reasoning** (no guessing)
* **Read before write**
* **Minimal, deterministic actions**
* **Markdown-based memory**
* **Safe file operations**

---

## 🔐 Safety

* All file operations restricted to `/workspace`
* Path traversal (`..`) blocked
* Optional command whitelisting recommended
* File size limits enforced

---

## 🧪 Example Workflow

```text
User: Analyze project structure

Agent:
→ list_files
→ read_file
→ extract patterns
→ write_to_file (/knowledge/project_map.md)
```

---

## 📈 Roadmap

### Phase 1 (Current)

* ✅ Tool loop
* ✅ File system tools
* ✅ Persistent memory

### Phase 2

* 🔄 Planner → Executor split
* 🔄 Self-reflection loop
* 🔄 Code auto-debugging

### Phase 3

* 🧠 Pattern merging & evolution
* 🧠 Multi-task execution
* 🧠 Knowledge graph

---

## ⚠️ Limitations

* No parallel tool execution
* Basic patching (string replace only)
* No semantic code understanding (yet)
* Shell execution can be unsafe if unrestricted

---

## 🧠 Vision

Agent_Unit_PIE aims to evolve into a system that:

* Continuously learns from data
* Builds a structured knowledge base
* Improves its reasoning over time

> From execution → to intelligence → to pattern awareness

---

## 🤝 Contributing

This is an experimental agent system.
Contributions, ideas, and improvements are welcome.

---

## 📜 License

MIT License (or define your own)
