AgentComponents.FileTree = {
  template: '#file-tree-tmpl',
  setup() {
    const store = AgentStore
    const entries = Vue.ref([])
    const expanded = Vue.reactive({})
    const children = Vue.reactive({})
    const loading = Vue.reactive({})
    const filter = Vue.ref('')
    const error = Vue.ref(null)
    const listRef = Vue.ref(null)

    async function loadDir(path) {
      loading[path || ''] = true
      try {
        const res = await fetch('/api/files/ls?path=' + encodeURIComponent(path || ''))
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Failed to list')
        return data.entries || []
      } catch (e) {
        error.value = String(e.message || e)
        return []
      } finally {
        loading[path || ''] = false
      }
    }

    async function refresh() {
      error.value = null
      allFiles.value = null
      entries.value = await loadDir('')
      for (const dir of Object.keys(expanded)) {
        if (expanded[dir]) children[dir] = await loadDir(dir)
      }
    }

    async function toggle(entry) {
      const path = entry.path
      expanded[path] = !expanded[path]
      if (expanded[path] && !children[path]) children[path] = await loadDir(path)
    }

    function open(path) {
      store.openFile(path)
    }

    function click(entry) {
      if (entry.type === 'dir') toggle(entry)
      else open(entry.path)
    }

    function isActive(path) { return store.activeFile === path }

    const rows = Vue.computed(() => {
      const out = []
      const walk = (list, depth) => {
        for (const e of list) {
          out.push({ ...e, depth })
          if (e.type === 'dir' && expanded[e.path] && children[e.path]) walk(children[e.path], depth + 1)
        }
      }
      walk(entries.value, 0)
      return out
    })

    const allFiles = Vue.ref(null)

    async function ensureAllFiles() {
      if (allFiles.value) return allFiles.value
      try {
        const res = await fetch('/api/files/workspace')
        const data = await res.json()
        allFiles.value = data.files || []
      } catch (_) { allFiles.value = [] }
      return allFiles.value
    }

    const filtered = Vue.computed(() => {
      const q = filter.value.trim().toLowerCase()
      if (!q) return null
      const list = allFiles.value || []
      return list.filter(p => p.toLowerCase().includes(q)).slice(0, 200).map(p => ({
        path: p, name: p.split('/').pop(), type: 'file', depth: 0,
      }))
    })

    const visibleRows = Vue.computed(() => filtered.value || rows.value)

    async function postJson(url, body) {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
      return data
    }

    async function newFile() {
      const path = window.prompt('New file path (relative to workspace):')
      if (!path || !path.trim()) return
      try {
        const data = await postJson('/api/files/write', { path: path.trim(), content: '' })
        error.value = null
        await refresh()
        const parts = data.path.split('/')
        parts.pop()
        let prefix = ''
        for (const part of parts) {
          prefix = prefix ? prefix + '/' + part : part
          expanded[prefix] = true
          if (!children[prefix]) children[prefix] = await loadDir(prefix)
        }
        store.openFile(data.path)
      } catch (e) { error.value = String(e.message || e) }
    }

    async function rename(row) {
      const next = window.prompt('Rename to:', row.path)
      if (!next || !next.trim() || next.trim() === row.path) return
      try {
        const data = await postJson('/api/files/rename', { path: row.path, new_path: next.trim() })
        store.renameTab(row.path, data.path)
        error.value = null
        await refresh()
      } catch (e) { error.value = String(e.message || e) }
    }

    async function remove(row) {
      if (!window.confirm(`Delete ${row.path}?`)) return
      try {
        await postJson('/api/files/delete', { path: row.path })
        store.discardPath(row.path)
        error.value = null
        await refresh()
      } catch (e) { error.value = String(e.message || e) }
    }

    const menu = Vue.reactive({ open: false, x: 0, y: 0, row: null })

    function openMenu(row, e) {
      menu.open = true
      menu.row = row
      menu.x = Math.min(e.clientX, window.innerWidth - 150)
      menu.y = Math.min(e.clientY, window.innerHeight - 96)
    }

    function closeMenu() {
      menu.open = false
      menu.row = null
    }

    function menuRename() {
      const row = menu.row
      closeMenu()
      if (row) rename(row)
    }

    function menuDelete() {
      const row = menu.row
      closeMenu()
      if (row) remove(row)
    }

    function fallbackCopy(text) {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      try { document.execCommand('copy') } catch (_) {}
      document.body.removeChild(ta)
    }

    function menuCopyPath() {
      const row = menu.row
      closeMenu()
      if (!row) return
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(row.path).catch(() => fallbackCopy(row.path))
      } else {
        fallbackCopy(row.path)
      }
    }

    async function reveal(row) {
      filter.value = ''
      const parts = row.path.split('/')
      if (row.type !== 'dir') parts.pop()
      let prefix = ''
      for (const part of parts) {
        prefix = prefix ? prefix + '/' + part : part
        expanded[prefix] = true
        if (!children[prefix]) children[prefix] = await loadDir(prefix)
      }
      if (row.type === 'dir') {
        expanded[row.path] = true
        if (!children[row.path]) children[row.path] = await loadDir(row.path)
      }
      await Vue.nextTick()
      const el = Array.from(listRef.value?.querySelectorAll('[data-path]') || [])
        .find(n => n.dataset.path === row.path)
      if (el) el.scrollIntoView({ block: 'nearest' })
    }

    function menuReveal() {
      const row = menu.row
      closeMenu()
      if (row) reveal(row)
    }

    function dismiss(e) {
      if (menu.open && !e.target.closest('.ft-context-menu')) closeMenu()
    }
    function onEsc(e) { if (e.key === 'Escape') closeMenu() }
    Vue.onMounted(() => {
      document.addEventListener('mousedown', dismiss)
      document.addEventListener('keydown', onEsc)
    })
    Vue.onBeforeUnmount(() => {
      document.removeEventListener('mousedown', dismiss)
      document.removeEventListener('keydown', onEsc)
    })

    Vue.watch(filter, (v) => { if (v.trim()) ensureAllFiles() })
    Vue.watch(() => store.treeVersion, () => { allFiles.value = null })

    Vue.watch(() => store.treeVersion, refresh)
    Vue.onMounted(refresh)

    return { store, listRef, visibleRows, expanded, filter, error, click, isActive, refresh, newFile, rename, remove, menu, openMenu, menuRename, menuDelete, menuCopyPath, menuReveal }
  }
}
