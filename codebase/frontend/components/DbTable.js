const DB_PAGE = 50

AgentComponents.DbTable = {
  template: '#db-table-tmpl',
  props: { path: { type: String, required: true } },
  setup(props) {
    const tables = Vue.ref([])
    const active = Vue.ref('')
    const offset = Vue.ref(0)
    const order = Vue.ref('')
    const dir = Vue.ref('asc')
    const loading = Vue.ref(false)
    const error = Vue.ref(null)
    const draft = Vue.ref(null)
    const editing = Vue.ref(null)
    const info = Vue.reactive({ columns: [], pk: [], rows: [], total: 0, readonly: true })

    const jsonOpts = (method, body) => ({
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    function qs(params) {
      return Object.entries(params)
        .filter(([, v]) => v !== '' && v !== null && v !== undefined)
        .map(([k, v]) => k + '=' + encodeURIComponent(v))
        .join('&')
    }

    async function api(url, opts) {
      const res = await fetch(url, opts)
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
      return data
    }

    function fail(e) { error.value = String(e.message || e) }

    async function loadInfo() {
      loading.value = true
      try {
        const data = await api('/api/db/info?path=' + encodeURIComponent(props.path))
        tables.value = data.tables || []
        if (!tables.value.some(t => t.name === active.value)) {
          active.value = tables.value.length ? tables.value[0].name : ''
        }
        error.value = null
      } catch (e) { fail(e) } finally { loading.value = false }
    }

    async function loadTable() {
      if (!active.value) {
        info.columns = []
        info.rows = []
        info.total = 0
        return
      }
      loading.value = true
      try {
        const data = await api('/api/db/table?' + qs({
          path: props.path, table: active.value, limit: DB_PAGE,
          offset: offset.value, order: order.value, dir: dir.value,
        }))
        info.columns = data.columns
        info.pk = data.pk
        info.rows = data.rows
        info.total = data.total
        info.readonly = !!data.readonly || !data.pk.length
        error.value = null
      } catch (e) { fail(e) } finally { loading.value = false }
    }

    async function reload() {
      await loadInfo()
      await loadTable()
    }

    function pick(name) {
      if (name === active.value) return
      draft.value = null
      editing.value = null
      offset.value = 0
      active.value = name
    }

    function sortBy(name) {
      if (order.value === name) dir.value = dir.value === 'asc' ? 'desc' : 'asc'
      else { order.value = name; dir.value = 'asc' }
      offset.value = 0
      loadTable()
    }

    function rowKey(row) {
      return JSON.stringify(info.pk.map(k => row[k]))
    }

    function isNull(v) { return v === null || v === undefined }
    function isBlob(v) { return typeof v === 'string' && v.startsWith('<blob ') }
    function cellText(v) { return isNull(v) ? 'NULL' : String(v) }
    function isEditing(row, col) {
      return !!(editing.value && editing.value.key === rowKey(row) && editing.value.col === col)
    }

    function startEdit(row, col, ev) {
      if (info.readonly || isBlob(row[col]) || isEditing(row, col)) return
      editing.value = { key: rowKey(row), col, text: isNull(row[col]) ? '' : String(row[col]), row }
      Vue.nextTick(() => {
        const el = ev.target.closest('td')?.querySelector('input')
        if (el) { el.focus(); el.select() }
      })
    }

    async function commitEdit() {
      const edit = editing.value
      if (!edit) return
      editing.value = null
      const pk = {}
      info.pk.forEach(k => { pk[k] = edit.row[k] })
      try {
        await api('/api/db/row', jsonOpts('PATCH', {
          path: props.path, table: active.value, pk, values: { [edit.col]: edit.text },
        }))
        await loadTable()
      } catch (e) {
        fail(e)
        editing.value = edit
      }
    }

    function addRow() {
      if (info.readonly) return
      editing.value = null
      const row = {}
      info.columns.forEach(c => { row[c.name] = '' })
      draft.value = row
    }

    async function saveDraft() {
      try {
        await api('/api/db/row', jsonOpts('POST', {
          path: props.path, table: active.value, values: { ...draft.value },
        }))
        draft.value = null
        await reload()
      } catch (e) { fail(e) }
    }

    async function removeRow(row) {
      if (!window.confirm('Delete this row?')) return
      const pk = {}
      info.pk.forEach(k => { pk[k] = row[k] })
      try {
        await api('/api/db/row', jsonOpts('DELETE', { path: props.path, table: active.value, pk }))
        if (info.rows.length === 1 && offset.value > 0) offset.value -= DB_PAGE
        await reload()
      } catch (e) { fail(e) }
    }

    function prevPage() { if (offset.value > 0) offset.value = Math.max(0, offset.value - DB_PAGE) }
    function nextPage() { if (offset.value + DB_PAGE < info.total) offset.value += DB_PAGE }

    Vue.watch(active, () => { draft.value = null; loadTable() })
    Vue.watch(offset, () => { editing.value = null; loadTable() })
    Vue.watch(() => props.path, () => {
      active.value = ''
      offset.value = 0
      order.value = ''
      draft.value = null
      editing.value = null
      loadInfo()
    })
    Vue.onMounted(loadInfo)

    return {
      path: Vue.computed(() => props.path), tables, active, info, offset, order, dir, loading,
      error, draft, editing, DB_PAGE, pick, sortBy, rowKey, cellText, isNull, isEditing,
      startEdit, commitEdit, addRow, saveDraft, removeRow, prevPage, nextPage, reload,
    }
  },
}
