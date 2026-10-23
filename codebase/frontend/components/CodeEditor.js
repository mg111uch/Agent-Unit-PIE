const CM_MODE_BY_EXT = {
  py: 'python', pyw: 'python',
  js: 'javascript', mjs: 'javascript', cjs: 'javascript', jsx: 'javascript',
  ts: 'javascript', tsx: 'javascript',
  html: 'htmlmixed', htm: 'htmlmixed', vue: 'htmlmixed',
  css: 'css', scss: 'css', less: 'css',
  json: 'javascript', md: 'markdown', markdown: 'markdown',
  xml: 'xml', svg: 'xml', yaml: 'yaml', yml: 'yaml',
  sh: 'shell', bash: 'shell', zsh: 'shell',
  c: 'clike', h: 'clike', cpp: 'clike', cc: 'clike', hpp: 'clike',
  java: 'clike', go: 'clike', rs: 'clike', kt: 'clike',
  sql: 'sql',
}

function cmModeFor(path) {
  if (!path) return null
  const ext = path.split('.').pop().toLowerCase()
  return CM_MODE_BY_EXT[ext] || null
}

AgentComponents.CodeEditor = {
  template: '#code-editor-tmpl',
  setup() {
    const store = AgentStore
    const hostRef = Vue.ref(null)
    let cm = null
    let applying = false
    let currentPath = null
    let ro = null

    function activeTab() { return store.tabFor(store.activeFile) }

    function stashCurrent() {
      if (!cm || !currentPath) return
      const tab = store.tabFor(currentPath)
      if (!tab) return
      const val = cm.getValue()
      if (tab.content !== val) {
        tab.content = val
        tab.dirty = val !== tab.saved
      }
    }

    function create() {
      if (cm || !hostRef.value || !window.CodeMirror) return
      cm = window.CodeMirror(hostRef.value, {
        value: '',
        mode: null,
        lineNumbers: true,
        lineWrapping: !!store.wordWrap,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: false,
        viewportMargin: 20,
        extraKeys: {
          'Ctrl-S': () => store.saveFile(),
          'Cmd-S': () => store.saveFile(),
          Tab: (editor) => editor.replaceSelection('    '),
        },
      })
      cm.on('change', () => {
        if (applying) return
        const tab = store.tabFor(currentPath)
        if (!tab) return
        tab.content = cm.getValue()
        tab.dirty = tab.content !== tab.saved
      })
      cm.setSize('100%', '100%')
    }

    function loadActive() {
      create()
      if (!cm) return
      if (currentPath !== store.activeFile) stashCurrent()
      const tab = activeTab()
      const nextPath = tab ? tab.path : null
      const sameDoc = currentPath === nextPath && cm.getValue() === (tab ? tab.content : '')
      currentPath = nextPath
      if (!sameDoc) {
        applying = true
        cm.setValue(tab ? tab.content : '')
        cm.clearHistory()
        applying = false
      }
      cm.setOption('mode', cmModeFor(currentPath))
      cm.refresh()
      const goto = store.pendingGoto
      if (goto && goto.path === currentPath) {
        store.pendingGoto = null
        const lastLine = Math.max(0, cm.lineCount() - 1)
        const line = Math.max(0, Math.min((goto.line || 1) - 1, lastLine))
        cm.setCursor({ line, ch: 0 })
        cm.scrollIntoView({ line, ch: 0 }, 80)
        cm.focus()
      }
    }

    Vue.watch(() => store.activeFile, () => Vue.nextTick(loadActive))
    Vue.watch(() => store.editorVersion, () => Vue.nextTick(loadActive))
    Vue.watch(() => store.wordWrap, (v) => { if (cm) cm.setOption('lineWrapping', !!v) })
    Vue.onMounted(() => {
      Vue.nextTick(() => {
        if (store.activeFile) loadActive()
        if (window.ResizeObserver && hostRef.value) {
          ro = new ResizeObserver(() => { if (cm) cm.refresh() })
          ro.observe(hostRef.value)
        }
      })
      window.addEventListener('keydown', onKeydown)
    })
    Vue.onBeforeUnmount(() => {
      stashCurrent()
      window.removeEventListener('keydown', onKeydown)
      if (ro) { ro.disconnect(); ro = null }
      if (cm) { cm.toTextArea?.(); cm = null }
    })

    function onKeydown(e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault()
        store.saveFile()
      }
    }

    const language = Vue.computed(() => cmModeFor(store.activeFile) || 'text')

    function tabName(path) {
      return path ? path.split('/').pop() : ''
    }

    function close(e, path) {
      e.stopPropagation()
      store.closeTab(path)
    }

    return { store, hostRef, language, tabName, close }
  }
}
