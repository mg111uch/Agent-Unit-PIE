function prettyJSON(val) {
  if (val == null) return ''
  if (typeof val === 'object') {
    try { return JSON.stringify(val, null, 2) } catch (_) { return String(val) }
  }
  try { return JSON.stringify(JSON.parse(val), null, 2) }
  catch (_) { return String(val) }
}

function sanitizeMarkdown(text) {
  if (!text) return ''
  return DOMPurify.sanitize(marked.parse(String(text)))
}

AgentComponents.CopyButton = {
  template: '#copy-button-tmpl',
  props: ['text', 'toolCalls'],
  setup(props) {
    const copied = Vue.ref(false)
    function _copyFallback(txt) {
      const ta = document.createElement('textarea')
      ta.value = txt
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      try { document.execCommand('copy') } catch (_) {}
      document.body.removeChild(ta)
    }
    function copy() {
      let txt = props.text || ''
      if (props.toolCalls && props.toolCalls.length) {
        txt += '\n\n' + props.toolCalls.map(t =>
          `[${t.tool}]\nInput: ${prettyJSON(t.input)}\nResult: ${prettyJSON(t.result)}`
        ).join('\n')
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(txt).catch(function() { _copyFallback(txt) })
      } else {
        _copyFallback(txt)
      }
      copied.value = true
      setTimeout(() => { copied.value = false }, 1500)
    }
    return { copied, copy }
  }
}

AgentComponents.ToolCallCard = {
  template: '#tool-call-card-tmpl',
  props: ['toolCall', 'parallel'],
  setup(props) {
    const expanded = Vue.ref(false)
    Vue.watch(() => props.toolCall?.result, (val) => {
      if (val) expanded.value = true
    }, { immediate: true })
    function formatInput(input) { return prettyJSON(input) }
    return { expanded, formatInput, renderResult: sanitizeMarkdown }
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

    function groupedToolCalls(calls) {
      const groups = {}
      for (const tc of calls) {
        if (!groups[tc.step]) groups[tc.step] = { step: tc.step, calls: [], count: 0, parallel: false }
        groups[tc.step].calls.push(tc)
        groups[tc.step].count++
      }
      for (const g of Object.values(groups)) { g.parallel = g.count > 1 }
      return Object.values(groups)
    }

    function formatCost(cost) {
      if (cost == null) return ''
      return '$' + Number(cost).toFixed(6)
    }

    return { store, scrollRef, anchorRef, suggestions, send, onQuestionSubmit, groupedToolCalls, formatCost, renderMarkdown: sanitizeMarkdown }
  }
}
