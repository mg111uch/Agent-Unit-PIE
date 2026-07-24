AgentComponents.CopyButton = {
  template: '#copy-button-tmpl',
  props: ['text', 'toolCalls'],
  setup() {
    const copied = Vue.ref(false)
    function copy(props) {
      let txt = props.text || ''
      if (props.toolCalls && props.toolCalls.length) {
        txt += '\n\n' + props.toolCalls.map(t => `[${t.tool}]\nInput: ${t.input}\nResult: ${t.result || ''}`).join('\n')
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
  setup() {
    const expanded = Vue.ref(false)
    function formatInput(input) {
      try { return JSON.stringify(JSON.parse(input), null, 2) }
      catch (_) { return input }
    }
    return { expanded, formatInput }
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
