function prettyJSON(val) {
  if (val == null) return ''
  if (typeof val === 'object') {
    try { return JSON.stringify(val, null, 2) } catch (_) { return String(val) }
  }
  try { return JSON.stringify(JSON.parse(val), null, 2) }
  catch (_) { return String(val) }
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

    function parseInput(raw) {
      if (!raw) return null
      if (typeof raw === 'object') return raw
      try { return JSON.parse(raw) } catch (_) { return null }
    }

    const target = Vue.computed(() => {
      const tc = props.toolCall
      if (!tc) return null
      if (!['Write', 'edit_file', 'cross_file_edit', 'undo_last_edit'].includes(tc.tool)) return null
      const inp = parseInput(tc.input)
      if (!inp || typeof inp !== 'object') return null
      let path = inp.path || inp.file_path || ''
      let line = Number(inp.line) || 0
      if (Array.isArray(inp.edits) && inp.edits.length) {
        const edit = inp.edits.find(e => e && (e.path || e.file_path)) || inp.edits[0]
        if (!path && edit) path = edit.path || edit.file_path || ''
        if (!line && edit) line = Number(edit.line) || 0
      }
      if (!path) return null
      if (!line && typeof tc.result === 'string') {
        const m = tc.result.match(/@@ -\d+(?:,\d+)? \+(\d+)/)
        if (m) line = parseInt(m[1], 10)
      }
      return { path, line: line || 1 }
    })

    function primary() {
      if (target.value) AgentStore.openFileAt(target.value.path, target.value.line)
      else expanded.value = !expanded.value
    }

    function formatInput(input) { return prettyJSON(input) }
    function showUsage() {
      return AgentStore.showToolTokenUsage && props.toolCall?.usage?.total_tokens
    }
    return { expanded, target, primary, formatInput, renderResult: renderMarkdown, showUsage, formatTokens }
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

    function onMarkdownClick(event) { handleMarkdownClick(event, scrollRef.value, '') }

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

    return { store, scrollRef, anchorRef, suggestions, send, onQuestionSubmit, onMarkdownClick, groupedToolCalls, formatCost, renderMarkdown, formatTokens }
  }
}
