const AgentStore = Vue.reactive({
  connected: false,
  messages: [],
  currentToolCall: null,
  pendingToolCount: 0,
  pendingQuestions: null,
  llmCallActive: false,
  error: null,
  sessionActive: false,
})

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
          tc.toolCalls.push({ ...AgentStore.currentToolCall, callId, ok: true, result: null })
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
        if (msg.full_content) fnl.content = msg.full_content
        AgentStore.currentToolCall = null
      }
      break
    case 'error':
      AgentStore.error = msg.message
      const ea = lastAssistant()
      if (ea) { ea.content += '\n[Error: ' + msg.message + ']'; ea.isStreaming = false; ea.isThinking = false }
      break
    case 'llm_call':
      AgentStore.llmCallActive = msg.status === 'start'
      break
    case 'question':
      AgentStore.pendingQuestions = msg.questions
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
