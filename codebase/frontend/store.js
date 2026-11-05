const CHAT_HISTORY_MAX = 50

function formatTokens(n) {
  const v = Number(n) || 0
  if (v < 1000) return String(v)
  if (v < 1000000) {
    const k = v / 1000
    return (k >= 100 ? k.toFixed(0) : k.toFixed(2)) + 'k'
  }
  return (v / 1000000).toFixed(2) + 'm'
}

const AgentStore = Vue.reactive({
  connected: false,
  messages: [],
  currentToolCall: null,
  pendingToolCount: 0,
  pendingQuestions: null,
  llmCallActive: false,
  error: null,
  sessionActive: false,
  chatHistory: [],
  historyIndex: -1,
  savedDraft: '',
  showToolTokenUsage: false,
  sessionTokens: 0,
  contextWindow: 0,
  activeFile: null,
  tabs: [],
  pendingGoto: null,
  editorError: null,
  editorVersion: 0,
  treeVersion: 0,
  saving: false,
  treeWidth: 240,
  chatWidth: 416,
  wordWrap: false,
  mdPreview: false,
  textSize: 110,
})

const _savedTree = parseInt(localStorage.getItem('agent_tree_width'), 10)
if (_savedTree >= 120) AgentStore.treeWidth = _savedTree
const _savedChat = parseInt(localStorage.getItem('agent_chat_width'), 10)
if (_savedChat >= 280) AgentStore.chatWidth = _savedChat
AgentStore.wordWrap = localStorage.getItem('agent_word_wrap') === '1'
AgentStore.mdPreview = localStorage.getItem('agent_md_preview') === '1'

const TEXT_SIZE_DEFAULT = 110
const TEXT_SIZE_MIN = 80
const TEXT_SIZE_MAX = 160
const _savedText = parseInt(localStorage.getItem('agent_text_size'), 10)
AgentStore.textSize = _savedText >= TEXT_SIZE_MIN && _savedText <= TEXT_SIZE_MAX ? _savedText : TEXT_SIZE_DEFAULT

// Root font-size drives rem-based Tailwind text; --text-scale covers the few
// fixed-px labels and CodeMirror so every surface resizes together.
AgentStore.setTextSize = (value) => {
  const next = Math.round(Math.min(TEXT_SIZE_MAX, Math.max(TEXT_SIZE_MIN, Number(value) || TEXT_SIZE_DEFAULT)))
  AgentStore.textSize = next
  localStorage.setItem('agent_text_size', String(next))
  const scale = next / 100
  document.documentElement.style.fontSize = (16 * scale) + 'px'
  document.documentElement.style.setProperty('--text-scale', String(scale))
}

AgentStore.adjustTextSize = (delta) => AgentStore.setTextSize(AgentStore.textSize + delta)

AgentStore.setTextSize(AgentStore.textSize)

AgentStore.startResize = (side, e) => {
  e.preventDefault()
  const startX = e.clientX
  const start = side === 'left' ? AgentStore.treeWidth : AgentStore.chatWidth
  const min = side === 'left' ? 160 : 300
  const max = () => side === 'left'
    ? Math.max(min, Math.min(520, window.innerWidth - 360))
    : Math.max(min, Math.min(760, window.innerWidth - 360))
  const move = (ev) => {
    const dx = ev.clientX - startX
    const raw = side === 'left' ? start + dx : start - dx
    const next = Math.round(Math.min(max(), Math.max(min, raw)))
    AgentStore[side === 'left' ? 'treeWidth' : 'chatWidth'] = next
  }
  const up = () => {
    document.removeEventListener('mousemove', move)
    document.removeEventListener('mouseup', up)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    const key = side === 'left' ? 'agent_tree_width' : 'agent_chat_width'
    localStorage.setItem(key, String(side === 'left' ? AgentStore.treeWidth : AgentStore.chatWidth))
  }
  document.addEventListener('mousemove', move)
  document.addEventListener('mouseup', up)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

AgentStore.toggleWordWrap = () => {
  AgentStore.wordWrap = !AgentStore.wordWrap
  localStorage.setItem('agent_word_wrap', AgentStore.wordWrap ? '1' : '0')
}

AgentStore.setMdPreview = (on) => {
  AgentStore.mdPreview = !!on
  localStorage.setItem('agent_md_preview', AgentStore.mdPreview ? '1' : '0')
}

AgentStore.toggleMdPreview = () => AgentStore.setMdPreview(!AgentStore.mdPreview)

const WRITE_TOOLS = new Set(['Write', 'edit_file', 'cross_file_edit', 'undo_last_edit', 'execute_command'])

AgentStore.tabFor = (path) => AgentStore.tabs.find(t => t.path === path) || null

AgentStore.editorDirty = Vue.computed(() => {
  const t = AgentStore.tabFor(AgentStore.activeFile)
  return !!(t && t.dirty)
})

AgentStore.activateTab = (path) => {
  if (!AgentStore.tabFor(path)) return
  AgentStore.activeFile = path
  AgentStore.editorError = null
  AgentStore.editorVersion++
}

const MAX_TABS = 3
const DB_EXTS = new Set(['db', 'sqlite', 'sqlite3'])

AgentStore.isDbPath = (path) => {
  const ext = (path || '').split('.').pop().toLowerCase()
  return DB_EXTS.has(ext)
}

// Keep the tab strip bounded: opening a new file retires the oldest tab.
AgentStore.trimTabs = (keep) => {
  while (AgentStore.tabs.length > MAX_TABS) {
    const idx = AgentStore.tabs.findIndex(t => t.path !== keep)
    if (idx === -1) break
    const tab = AgentStore.tabs[idx]
    if (tab.dirty && !window.confirm(`Discard unsaved changes to ${tab.path}?`)) break
    AgentStore.tabs.splice(idx, 1)
    if (AgentStore.activeFile === tab.path) {
      AgentStore.activeFile = AgentStore.tabs[AgentStore.tabs.length - 1]?.path || null
    }
  }
}

AgentStore.openFile = async (path) => {
  if (!path) return null
  AgentStore.editorError = null
  if (AgentStore.tabFor(path)) {
    AgentStore.activateTab(path)
    return path
  }
  if (AgentStore.isDbPath(path)) {
    // SQLite files are binary: the tree viewer reads them over /api/db/*.
    AgentStore.tabs.push({ path, content: '', saved: '', dirty: false, kind: 'db' })
    AgentStore.trimTabs(path)
    AgentStore.activeFile = path
    AgentStore.editorVersion++
    return path
  }
  try {
    const res = await fetch('/api/files/read?path=' + encodeURIComponent(path))
    const data = await res.json()
    if (data.error) { AgentStore.editorError = data.error; return null }
    const full = data.path || path
    AgentStore.tabs.push({ path: full, content: data.content, saved: data.content, dirty: false })
    AgentStore.trimTabs(full)
    AgentStore.activeFile = full
    AgentStore.editorVersion++
    return full
  } catch (e) {
    AgentStore.editorError = String(e.message || e)
    return null
  }
}

AgentStore.openFileAt = async (path, line) => {
  const full = await AgentStore.openFile(path)
  if (!full) return
  AgentStore.pendingGoto = { path: full, line: Math.max(1, line || 1) }
  AgentStore.editorVersion++
}

AgentStore.closeTab = (path) => {
  const idx = AgentStore.tabs.findIndex(t => t.path === path)
  if (idx === -1) return
  const tab = AgentStore.tabs[idx]
  if (tab.dirty && !window.confirm(`Discard unsaved changes to ${path}?`)) return
  AgentStore.tabs.splice(idx, 1)
  if (AgentStore.activeFile === path) {
    const next = AgentStore.tabs[idx] || AgentStore.tabs[idx - 1] || null
    AgentStore.activeFile = next ? next.path : null
    AgentStore.editorVersion++
  }
}

AgentStore.closeTabSilent = (path) => {
  const idx = AgentStore.tabs.findIndex(t => t.path === path)
  if (idx === -1) return
  AgentStore.tabs.splice(idx, 1)
  if (AgentStore.activeFile === path) {
    const next = AgentStore.tabs[idx] || AgentStore.tabs[idx - 1] || null
    AgentStore.activeFile = next ? next.path : null
    AgentStore.editorVersion++
  }
}

AgentStore.discardPath = (path) => {
  const removedActive = AgentStore.activeFile === path || (AgentStore.activeFile && AgentStore.activeFile.startsWith(path + '/'))
  const keep = AgentStore.tabs.filter(t => t.path !== path && !t.path.startsWith(path + '/'))
  AgentStore.tabs.splice(0, AgentStore.tabs.length, ...keep)
  if (removedActive) {
    const next = AgentStore.tabs[AgentStore.tabs.length - 1] || null
    AgentStore.activeFile = next ? next.path : null
    AgentStore.editorVersion++
  }
}

AgentStore.renameTab = (oldPath, newPath) => {
  for (const tab of AgentStore.tabs) {
    if (tab.path === oldPath) tab.path = newPath
    else if (tab.path.startsWith(oldPath + '/')) tab.path = newPath + tab.path.slice(oldPath.length)
  }
  if (AgentStore.activeFile === oldPath) AgentStore.activeFile = newPath
  else if (AgentStore.activeFile && AgentStore.activeFile.startsWith(oldPath + '/')) {
    AgentStore.activeFile = newPath + AgentStore.activeFile.slice(oldPath.length)
  }
  AgentStore.editorVersion++
}

AgentStore.resetEditor = () => {
  AgentStore.tabs.splice(0, AgentStore.tabs.length)
  AgentStore.activeFile = null
  AgentStore.pendingGoto = null
  AgentStore.editorError = null
  AgentStore.editorVersion++
}

AgentStore.reloadCleanTabs = async () => {
  let changed = false
  for (const tab of [...AgentStore.tabs]) {
    if (tab.dirty || tab.kind === 'db') continue
    try {
      const res = await fetch('/api/files/read?path=' + encodeURIComponent(tab.path))
      const data = await res.json()
      if (data.error) continue
      if (tab.content !== data.content) changed = true
      tab.content = data.content
      tab.saved = data.content
      tab.dirty = false
    } catch (_) {}
  }
  if (changed) AgentStore.editorVersion++
}

AgentStore.saveFile = async () => {
  const tab = AgentStore.tabFor(AgentStore.activeFile)
  if (!tab || AgentStore.saving || tab.kind === 'db') return
  AgentStore.saving = true
  AgentStore.editorError = null
  try {
    const res = await fetch('/api/files/write', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: tab.path, content: tab.content }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.detail || `Save failed (${res.status})`)
    tab.saved = tab.content
    tab.dirty = false
    AgentStore.treeVersion++
  } catch (e) {
    AgentStore.editorError = String(e.message || e)
  } finally {
    AgentStore.saving = false
  }
}

AgentStore.saveToChatHistory = (text) => {
  if (!text || !text.trim()) return
  AgentStore.chatHistory.unshift(text.trim())
  if (AgentStore.chatHistory.length > CHAT_HISTORY_MAX) AgentStore.chatHistory.length = CHAT_HISTORY_MAX
  AgentStore.historyIndex = -1
  AgentStore.savedDraft = ''
  localStorage.setItem('agent_chat_history', JSON.stringify(AgentStore.chatHistory))
}

const saved = localStorage.getItem('agent_chat_history')
if (saved) AgentStore.chatHistory = JSON.parse(saved).slice(0, CHAT_HISTORY_MAX)

AgentStore.isBusy = Vue.computed(() =>
  AgentStore.pendingToolCount > 0
  || !!AgentStore.pendingQuestions
  || AgentStore.messages.some(m => m.role === 'assistant' && m.isStreaming)
)

AgentStore.handleMessage = (msg) => {
  AgentStore.error = null
  switch (msg.type) {
    case 'connected':
      AgentStore.connected = true
      AgentStore.showToolTokenUsage = !!msg.show_tool_token_usage
      AgentStore.contextWindow = msg.context_window || 0
      break
    case 'status':
      const last = lastAssistant()
      if (last) last.isThinking = msg.status === 'thinking'
      break
    case 'tool_call':
      AgentStore.currentToolCall = { tool: msg.tool, input: msg.input, step: msg.step, usage: msg.usage || null }
      AgentStore.pendingToolCount++
      const tc = lastAssistant()
      if (tc) {
        tc.toolCalls = tc.toolCalls || []
        const callId = msg.call_id || `${msg.step}_${msg.tool}`
        const exist = tc.toolCalls.find(t => t.callId === callId)
        if (!exist) {
          const entry = { ...AgentStore.currentToolCall, callId, ok: true, result: null, usage: msg.usage || null }
          const sameStep = tc.toolCalls.filter(t => t.step === msg.step)
          if (sameStep.length > 0) {
            entry.parallel = true
            sameStep.forEach(t => t.parallel = true)
          }
          tc.toolCalls.push(entry)
        }
      }
      break
    case 'tool_result':
      AgentStore.currentToolCall = null
      AgentStore.pendingToolCount = Math.max(0, AgentStore.pendingToolCount - 1)
      const tr = lastAssistant()
      if (tr && tr.toolCalls) {
        const callId = msg.call_id || `${msg.step}_${msg.tool}`
        const hit = tr.toolCalls.find(t => t.callId === callId)
        if (hit) {
          hit.result = msg.result
          hit.ok = msg.ok !== false
          if (msg.usage) hit.usage = msg.usage
        }
      }
      if (WRITE_TOOLS.has(msg.tool)) {
        AgentStore.treeVersion++
        AgentStore.reloadCleanTabs()
      }
      break
    case 'stream_chunk':
      const sc = lastAssistant()
      if (sc) {
        sc.content += msg.content
        sc.isThinking = false
      }
      break
    case 'final':
      const fnl = lastAssistant()
      if (fnl) {
        fnl.isStreaming = false
        fnl.isThinking = false
        fnl.pendingQuestion = false
        if (msg.full_content) fnl.content = msg.full_content
        AgentStore.currentToolCall = null
      }
      AgentStore.pendingToolCount = 0
      AgentStore.pendingQuestions = null
      break
    case 'error':
      AgentStore.error = msg.message
      const ea = lastAssistant()
      if (ea) { ea.content += '\n[Error: ' + msg.message + ']'; ea.isStreaming = false; ea.isThinking = false }
      AgentStore.pendingToolCount = 0
      AgentStore.pendingQuestions = null
      break
    case 'llm_call':
      AgentStore.llmCallActive = msg.status === 'start'
      if (msg.status === 'end') {
        const last = lastAssistant()
        if (last) {
          if (msg.usage) {
            last.usage = last.usage || {}
            last.usage.total_tokens = (last.usage.total_tokens || 0) + (msg.usage.total_tokens || 0)
            last.usage.prompt_tokens = (last.usage.prompt_tokens || 0) + (msg.usage.prompt_tokens || 0)
            last.usage.completion_tokens = (last.usage.completion_tokens || 0) + (msg.usage.completion_tokens || 0)
            last.usage.estimated_cost = (last.usage.estimated_cost || 0) + (msg.usage.estimated_cost || 0)
            AgentStore.sessionTokens += msg.usage.total_tokens || 0
          }
          if (msg.latency_seconds != null) last.latency = msg.latency_seconds
          if (msg.retries) last.retries = msg.retries
        }
      }
      break
    case 'question':
      AgentStore.pendingQuestions = msg.questions
      const qa = lastAssistant()
      if (qa) { qa.isThinking = false; qa.pendingQuestion = true }
      break
    case 'summary':
      const sm = lastAssistant()
      if (sm) {
        sm.totalSteps = msg.total_steps
        sm.cacheHits = msg.cache_hits
        sm.cacheMisses = msg.cache_misses
      }
      break
    case 'reset':
      AgentStore.messages = []
      AgentStore.currentToolCall = null
      AgentStore.pendingToolCount = 0
      AgentStore.pendingQuestions = null
      AgentStore.error = null
      AgentStore.sessionTokens = 0
      break
  }
}

function lastAssistant() {
  for (let i = AgentStore.messages.length - 1; i >= 0; i--)
    if (AgentStore.messages[i].role === 'assistant') return AgentStore.messages[i]
  return null
}
