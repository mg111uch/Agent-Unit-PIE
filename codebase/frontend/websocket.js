let ws = null
let reconnectTimer = null
let serverUrl = window.location.host

function connect() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${proto}//${serverUrl}/ws/agent`
  ws = new WebSocket(url)
  ws.onopen = () => { AgentStore.connected = true }
  ws.onclose = () => {
    AgentStore.connected = false
    if (!reconnectTimer) reconnectTimer = setTimeout(() => { reconnectTimer = null; connect() }, 3000)
  }
  ws.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data)
      if (msg.type === 'question') console.log('[ws] question received, n=', (msg.questions || []).length)
      AgentStore.handleMessage(msg)
    } catch (err) {
      console.error('[ws] handleMessage failed:', err, e.data)
    }
  }
}

function sendJson(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj))
}

AgentStore.sendMessage = (content) => {
  AgentStore.saveToChatHistory(content)
  AgentStore.messages.push({ id: 'user-' + Date.now(), role: 'user', content, timestamp: Date.now() })
  AgentStore.messages.push({ id: 'assistant-' + Date.now(), role: 'assistant', content: '', isStreaming: true, isThinking: true, toolCalls: [] })
  AgentStore.sessionActive = true
  sendJson({ type: 'chat', content })
}

AgentStore.sendCancel = () => {
  AgentStore.pendingQuestions = null
  AgentStore.pendingToolCount = 0
  sendJson({ type: 'cancel' })
}

AgentStore.resetConversation = () => {
  AgentStore.messages = []
  AgentStore.currentToolCall = null
  AgentStore.pendingToolCount = 0
  AgentStore.pendingQuestions = null
  AgentStore.error = null
  AgentStore.sessionActive = false
  sendJson({ type: 'reset' })
}

AgentStore.submitQuestionAnswer = (answers) => {
  sendJson({ type: 'question_answer', answers })
  AgentStore.pendingQuestions = null
}

AgentStore.sendSlash = (command, args) => {
  AgentStore.saveToChatHistory('/' + command + ' ' + args)
  AgentStore.messages.push({ id: 'user-' + Date.now(), role: 'user', content: '/' + command + ' ' + args, timestamp: Date.now() })
  AgentStore.messages.push({ id: 'assistant-' + Date.now(), role: 'assistant', content: '', isStreaming: true, isThinking: true, toolCalls: [] })
  AgentStore.sessionActive = true
  sendJson({ type: 'slash', command, args })
}

connect()
