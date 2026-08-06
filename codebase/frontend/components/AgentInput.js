AgentComponents.AgentInput = {
  template: '#agent-input-tmpl',
  setup() {
    const store = AgentStore
    const input = Vue.ref('')
    const taRef = Vue.ref(null)
    const slashOpen = Vue.ref(false)
    const atOpen = Vue.ref(false)
    const slashIndex = Vue.ref(0)
    const fileIndex = Vue.ref(0)
    const filePaths = Vue.ref([])
    const filteredFiles = Vue.ref([])
    const cursorPos = Vue.ref(0)
    const insertedFilePaths = Vue.ref(new Set())

    function syncScroll() {
      const overlay = taRef.value?.previousElementSibling
      if (overlay) overlay.scrollTop = taRef.value.scrollTop
    }

    function highlightInput() {
      let html = input.value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
      slashCommands.forEach(c => {
        const re = new RegExp('(^|\\n)(' + c.command.replace('/', '\\/') + ')', 'g')
        html = html.replace(re, '$1<span style="color:#38bdf8">$2</span>')
      })
      insertedFilePaths.value.forEach(fp => {
        const e = fp.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        const re = new RegExp('@\\b(' + e + ')\\b', 'g')
        html = html.replace(re, '<span style="color:#d97706">$&</span>')
      })
      return html.replace(/\n/g, '<br>')
    }

    function isHiddenPath(p) {
      return p.split('/').some(seg => seg.startsWith('.'))
    }

    function scrollFileActive() {
      setTimeout(() => {
        const el = document.querySelector('.file-dropdown')
        if (!el) return
        const btn = el.querySelector('.file-active')
        if (!btn) return
        const btnTop = btn.offsetTop
        const btnBottom = btnTop + btn.offsetHeight
        if (btnTop < el.scrollTop) el.scrollTop = btnTop
        if (btnBottom > el.scrollTop + el.clientHeight) el.scrollTop = btnBottom - el.clientHeight
      }, 0)
    }

    const slashCommands = [
      { command: '/new', desc: 'Start a new session' },
      { command: '/argu explore', desc: 'Argument exploration' },
      { command: '/auto', desc: 'Auto research' },
    ]

    Vue.onMounted(async () => {
      try {
        const res = await fetch('/api/files/workspace')
        const data = await res.json()
        if (data.files) filePaths.value = data.files.filter(p => !isHiddenPath(p))
      } catch (_) {}
      if (filePaths.value.length === 0) {
        try {
          const res = await fetch('/api/files/tree')
          const data = await res.json()
          filePaths.value = flattenTree(data.tree || [], '').filter(p => !isHiddenPath(p))
        } catch (_) {}
      }
    })

    function flattenTree(tree, prefix) {
      let result = []
      for (const item of tree) {
        const path = prefix ? prefix + '/' + item.name : item.name
        if (item.type === 'file') result.push(path)
        if (item.children) result = result.concat(flattenTree(item.children, path))
      }
      return result
    }

    function onInput() {
      const val = input.value
      const pos = taRef.value?.selectionStart || val.length
      slashOpen.value = false
      atOpen.value = false

      const lineStart = val.lastIndexOf('\n', pos - 1) + 1
      const beforeCursor = val.slice(lineStart, pos)

      if (beforeCursor.startsWith('/')) {
        const query = beforeCursor.slice(1).toLowerCase()
        slashOpen.value = true
        slashIndex.value = 0
      } else if (beforeCursor.includes('@')) {
        const atIdx = beforeCursor.lastIndexOf('@')
        const query = beforeCursor.slice(atIdx + 1).toLowerCase()
        atOpen.value = true
        fileIndex.value = 0
        filteredFiles.value = filePaths.value.filter(f => f.toLowerCase().includes(query))
      }
    }

    function onKeydown(e) {
      if (slashOpen.value) {
        if (e.key === 'ArrowDown') { e.preventDefault(); slashIndex.value = Math.min(slashIndex.value + 1, slashCommands.length - 1); return }
        if (e.key === 'ArrowUp') { e.preventDefault(); slashIndex.value = Math.max(slashIndex.value - 1, 0); return }
        if ((e.key === 'Enter' || e.key === 'Tab') && slashOpen.value) { e.preventDefault(); selectSlash(slashCommands[slashIndex.value]); return }
        if (e.key === 'Escape') { slashOpen.value = false; return }
      }
      if (atOpen.value) {
        if (e.key === 'ArrowDown') { e.preventDefault(); fileIndex.value = Math.min(fileIndex.value + 1, filteredFiles.value.length - 1); scrollFileActive(); return }
        if (e.key === 'ArrowUp') { e.preventDefault(); fileIndex.value = Math.max(fileIndex.value - 1, 0); scrollFileActive(); return }
        if ((e.key === 'Enter' || e.key === 'Tab') && atOpen.value) { e.preventDefault(); insertFile(filteredFiles.value[fileIndex.value]); return }
        if (e.key === 'Escape') { atOpen.value = false; return }
      }
      if (e.key === 'ArrowUp' && !slashOpen.value && !atOpen.value) {
        e.preventDefault()
        if (store.historyIndex === -1) store.savedDraft = input.value
        if (store.historyIndex < store.chatHistory.length - 1) {
          store.historyIndex++
          input.value = store.chatHistory[store.historyIndex]
        }
        return
      }
      if (e.key === 'ArrowDown' && store.historyIndex !== -1 && !slashOpen.value && !atOpen.value) {
        e.preventDefault()
        if (store.historyIndex === 0) {
          store.historyIndex = -1
          input.value = store.savedDraft || ''
        } else {
          store.historyIndex--
          input.value = store.chatHistory[store.historyIndex]
        }
        return
      }
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() }
    }

    function selectSlash(cmd) {
      const val = input.value
      const pos = taRef.value?.selectionStart || val.length
      const lineStart = val.lastIndexOf('\n', pos - 1) + 1
      const before = val.slice(0, lineStart)
      const after = val.slice(pos)
      input.value = before + cmd.command + ' ' + after
      slashOpen.value = false
      Vue.nextTick(() => { taRef.value?.focus() })
    }

    function insertFile(path) {
      const val = input.value
      const pos = taRef.value?.selectionStart || val.length
      const lineStart = val.lastIndexOf('\n', pos - 1) + 1
      const beforeCursor = val.slice(lineStart, pos)
      const atIdx = beforeCursor.lastIndexOf('@')
      const insertPos = lineStart + atIdx
      const before = val.slice(0, insertPos)
      const after = val.slice(pos)
      input.value = before + '@' + path + ' ' + after
      insertedFilePaths.value.add(path)
      atOpen.value = false
      Vue.nextTick(() => { taRef.value?.focus() })
    }

    function submit() {
      const text = input.value.trim()
      if (!text || !store.connected) return
      if (text.startsWith('/new') || text.startsWith('/clear') || text.startsWith('/reset')) {
        store.resetConversation()
        const parts = text.split(' ')
        if (parts[0] === '/new' && parts.length > 1) {
          store.sendMessage(parts.slice(1).join(' '))
        }
        input.value = ''; slashOpen.value = false; atOpen.value = false
        return
      }
      if (text.startsWith('/argu')) {
        const args = text.slice(6).trim()
        if (args) store.sendSlash('argu explore', args)
        input.value = ''; slashOpen.value = false; atOpen.value = false
        return
      }
      if (text.startsWith('/auto')) {
        const args = text.slice(5).trim()
        if (args) store.sendSlash('auto', args)
        input.value = ''; slashOpen.value = false; atOpen.value = false
        return
      }
      store.sendMessage(text)
      input.value = ''; slashOpen.value = false; atOpen.value = false
      insertedFilePaths.value = new Set()
      Vue.nextTick(() => { if (taRef.value) { taRef.value.style.height = 'auto' }; taRef.value?.focus() })
    }

    const tokenLinePct = Vue.computed(() => {
      if (!store.contextWindow) return '0%'
      return Math.min(100, (store.sessionTokens / store.contextWindow) * 100).toLocaleString('en-US', { maximumFractionDigits: 2 }) + '%'
    })

    return { store, input, taRef, slashOpen, atOpen, slashIndex, fileIndex, filteredFiles, slashCommands, onInput, onKeydown, selectSlash, insertFile, submit, highlightInput, syncScroll, formatTokens, tokenLinePct }
  }
}
