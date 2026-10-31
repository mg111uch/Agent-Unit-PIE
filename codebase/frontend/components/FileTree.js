AgentComponents.FileTree = {
  template: '#file-tree-tmpl',
  setup() {
    const store = AgentStore
    const projects = Vue.ref([])
    const expanded = Vue.reactive({})
    const children = Vue.reactive({})
    const loading = Vue.reactive({})
    const filter = Vue.ref('')
    const error = Vue.ref(null)
    const listRef = Vue.ref(null)
    const allFiles = Vue.ref(null)

    const keyOf = (pid, path) => (pid || '') + '|' + (path || '')
    const activePid = Vue.computed(() => (projects.value.find(p => p.active) || {}).id || '')
    const roots = Vue.computed(() => [...projects.value].sort((a, b) => a.name.localeCompare(b.name)))

    async function loadProjects() {
      try {
        const res = await fetch('/api/projects')
        const data = await res.json()
        projects.value = data.projects || []
      } catch (_) {}
    }

    function hasDirtyTabs() { return store.tabs.some(t => t.dirty) }

    // Only one project can own the agent workspace; claim it before any
    // filesystem call so ls/read/write resolve inside the right root.
    async function ensureActive(pid) {
      if (!pid || activePid.value === pid) return true
      if (hasDirtyTabs() && !window.confirm('Discard unsaved changes and switch project?')) return false
      try {
        const res = await fetch('/api/projects/activate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: pid }),
        })
        const data = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(data.detail || 'Switch failed')
        store.resetEditor()
        projects.value = projects.value.map(p => ({ ...p, active: p.id === pid }))
        error.value = null
        return true
      } catch (e) {
        error.value = String(e.message || e)
        return false
      }
    }

    async function loadDir(pid, path) {
      const key = keyOf(pid, path)
      loading[key] = true
      try {
        if (!(await ensureActive(pid))) return []
        const res = await fetch('/api/files/ls?path=' + encodeURIComponent(path || ''))
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Failed to list')
        return data.entries || []
      } catch (e) {
        error.value = String(e.message || e)
        return []
      } finally {
        loading[key] = false
      }
    }

    async function refresh() {
      error.value = null
      allFiles.value = null
      const pid = activePid.value
      if (!pid) return
      const rootKey = keyOf(pid, '')
      const rootOpen = expanded[rootKey] !== false
      // Always re-list the root and every expanded dir: cached listings go
      // stale as soon as a file is created/renamed/deleted on disk.
      children[rootKey] = await loadDir(pid, '')
      if (rootOpen) expanded[rootKey] = true
      for (const k of Object.keys(expanded)) {
        if (!expanded[k]) continue
        const sep = k.indexOf('|')
        const p = k.slice(0, sep)
        const path = k.slice(sep + 1)
        if (p !== pid || !path) continue
        children[k] = await loadDir(p, path)
      }
      // Collapsed dirs keep no stale cache; they re-list when expanded.
      for (const k of Object.keys(children)) {
        if (k.startsWith(pid + '|') && !expanded[k]) delete children[k]
      }
    }

    async function toggle(row) {
      const key = keyOf(row.pid, row.path)
      if (expanded[key]) { expanded[key] = false; return }
      if (!children[key]) children[key] = await loadDir(row.pid, row.path)
      expanded[key] = true
    }

    async function open(pid, path) {
      if (await ensureActive(pid)) store.openFile(path)
    }

    async function click(row) {
      if (row.type === 'dir') await toggle(row)
      else await open(row.pid, row.path)
    }

    function isActive(path, pid) {
      return pid === activePid.value && store.activeFile === path
    }

    const rows = Vue.computed(() => {
      const out = []
      const walk = (list, depth, pid) => {
        for (const e of list) {
          out.push({ ...e, depth, pid })
          const k = keyOf(pid, e.path)
          if (e.type === 'dir' && expanded[k] && children[k]) walk(children[k], depth + 1, pid)
        }
      }
      for (const p of roots.value) {
        out.push({ path: '', name: p.name, type: 'dir', depth: 0, pid: p.id, isRoot: true, active: p.active })
        const k = keyOf(p.id, '')
        if (expanded[k] && children[k]) walk(children[k], 1, p.id)
      }
      return out
    })

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
        path: p, name: p.split('/').pop(), type: 'file', depth: 1, pid: activePid.value,
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
        const pid = activePid.value
        if (pid) {
          // Expand the containing folders first so refresh() re-lists them and
          // the newly created file shows up immediately.
          const dirs = data.path.split('/')
          dirs.pop()
          expanded[keyOf(pid, '')] = true
          let prefix = ''
          for (const part of dirs) {
            prefix = prefix ? prefix + '/' + part : part
            expanded[keyOf(pid, prefix)] = true
          }
        }
        await refresh()
        store.openFile(data.path)
      } catch (e) { error.value = String(e.message || e) }
    }

    async function addProject() {
      const path = window.prompt('Project folder (absolute path):', '/home/')
      if (!path || !path.trim()) return
      try {
        await postJson('/api/projects', { path: path.trim() })
        error.value = null
        await loadProjects()
      } catch (e) { error.value = String(e.message || e) }
    }

    function purge(pid) {
      const pre = pid + '|'
      for (const k of Object.keys(expanded)) if (k.startsWith(pre)) delete expanded[k]
      for (const k of Object.keys(children)) if (k.startsWith(pre)) delete children[k]
    }

    async function removeProject(pid) {
      const p = projects.value.find(x => x.id === pid)
      if (!p || pid === 'default') return
      if (!window.confirm(`Remove ${p.name} from the tree? (files are not deleted)`)) return
      try {
        const res = await fetch('/api/projects/' + encodeURIComponent(pid), { method: 'DELETE' })
        const data = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(data.detail || 'Remove failed')
        error.value = null
        const wasActive = p.active
        purge(pid)
        await loadProjects()
        if (wasActive) { store.resetEditor(); await refresh() }
      } catch (e) { error.value = String(e.message || e) }
    }

    async function rename(row) {
      if (!(await ensureActive(row.pid))) return
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
      if (!(await ensureActive(row.pid))) return
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
      if (row && !row.isRoot) rename(row)
    }

    function menuDelete() {
      const row = menu.row
      closeMenu()
      if (row && !row.isRoot) remove(row)
    }

    function menuSetActive() {
      const row = menu.row
      closeMenu()
      if (row && row.isRoot) ensureActive(row.pid)
    }

    function menuRemoveProject() {
      const row = menu.row
      closeMenu()
      if (row && row.isRoot) removeProject(row.pid)
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
      const project = projects.value.find(p => p.id === row.pid)
      const full = row.isRoot ? (project ? project.path : '') : row.path
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(full).catch(() => fallbackCopy(full))
      } else {
        fallbackCopy(full)
      }
    }

    async function reveal(row) {
      filter.value = ''
      const pid = row.pid
      if (!(await ensureActive(pid))) return
      const parts = row.path.split('/')
      if (row.type !== 'dir') parts.pop()
      let prefix = ''
      const rootKey = keyOf(pid, '')
      if (!children[rootKey]) children[rootKey] = await loadDir(pid, '')
      expanded[rootKey] = true
      for (const part of parts) {
        prefix = prefix ? prefix + '/' + part : part
        const k = keyOf(pid, prefix)
        expanded[k] = true
        if (!children[k]) children[k] = await loadDir(pid, prefix)
      }
      await Vue.nextTick()
      const el = Array.from(listRef.value?.querySelectorAll('[data-key]') || [])
        .find(n => n.dataset.key === keyOf(pid, row.path))
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
    Vue.onMounted(async () => {
      await loadProjects()
      await refresh()
    })

    return {
      store, listRef, projects, roots, visibleRows, expanded, filter, error, click, isActive,
      refresh, newFile, addProject, removeProject, menu, openMenu, menuRename, menuDelete, menuSetActive,
      menuRemoveProject, menuCopyPath, menuReveal, keyOf,
    }
  }
}
