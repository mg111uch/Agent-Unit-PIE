const CHAT_HISTORY_MAX = 50

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
})

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
      break
    case 'status':
      const last = lastAssistant()
      if (last) last.isThinking = msg.status === 'thinking'
      break
    case 'tool_call':
      AgentStore.currentToolCall = { tool: msg.tool, input: msg.input, step: msg.step }
      AgentStore.pendingToolCount++
      const tc = lastAssistant()
      if (tc) {
        tc.toolCalls = tc.toolCalls || []
        const callId = msg.call_id || `${msg.step}_${msg.tool}`
        const exist = tc.toolCalls.find(t => t.callId === callId)
        if (!exist) {
          const entry = { ...AgentStore.currentToolCall, callId, ok: true, result: null }
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
        }
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
          if (msg.usage) last.usage = msg.usage
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
      break
  }
}

function lastAssistant() {
  for (let i = AgentStore.messages.length - 1; i >= 0; i--)
    if (AgentStore.messages[i].role === 'assistant') return AgentStore.messages[i]
  return null
}
