AgentComponents.CopyButton = {
  template: '#copy-button-tmpl',
  props: ['text', 'toolCalls'],
  setup(props) {
    const copied = Vue.ref(false)
    function pretty(val) {
      if (val == null) return ''
      if (typeof val === 'object') {
        try { return JSON.stringify(val, null, 2) } catch (_) { return String(val) }
      }
      try { return JSON.stringify(JSON.parse(val), null, 2) }
      catch (_) { return String(val) }
    }
    function copy() {
      let txt = props.text || ''
      if (props.toolCalls && props.toolCalls.length) {
        txt += '\n\n' + props.toolCalls.map(t =>
          `[${t.tool}]\nInput: ${pretty(t.input)}\nResult: ${pretty(t.result)}`
        ).join('\n')
      }
      navigator.clipboard.writeText(txt)
      copied.value = true
      setTimeout(() => { copied.value = false }, 1500)
    }
    return { copied, copy }
  }
}

AgentComponents.ToolCallCard = {
  template: '#tool-call-card-tmpl',
  props: ['toolCall'],
  setup(props) {
    const expanded = Vue.ref(false)
    Vue.watch(() => props.toolCall?.result, (val) => {
      if (val) expanded.value = true
    }, { immediate: true })
    function formatValue(val) {
      if (val == null) return ''
      if (typeof val === 'object') {
        try { return JSON.stringify(val, null, 2) } catch (_) { return String(val) }
      }
      try { return JSON.stringify(JSON.parse(val), null, 2) }
      catch (_) { return String(val) }
    }
    function formatInput(input) { return formatValue(input) }
    function formatResult(result) { return formatValue(result) }
    return { expanded, formatInput, formatResult }
  }
}

AgentComponents.AgentChat = {
  template: '#agent-chat-tmpl',
  setup() {
    const store = AgentStore
    const scrollRef = Vue.ref(null)
    const anchorRef = Vue.ref(null)
    const suggestions = [
      'Explain this repo structure',
      'Find and fix a bug',
      'Add a new feature',
      'Write tests for a module'
    ]

    Vue.watch([() => store.messages.length, () => store.currentToolCall], () => {
      Vue.nextTick(() => { anchorRef.value?.scrollIntoView({ behavior: 'smooth' }) })
    }, { deep: true })

    function send(text) { store.sendMessage(text) }

    function onQuestionSubmit(answers) { store.submitQuestionAnswer(answers) }

    return { store, scrollRef, anchorRef, suggestions, send, onQuestionSubmit }
  }
}
