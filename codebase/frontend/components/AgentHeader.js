AgentComponents.AgentHeader = {
  template: '#agent-header-tmpl',
  setup() {
    const store = AgentStore
    const catalog = Vue.ref({ active: null })
    const open = Vue.ref(false)
    const switchError = Vue.ref(null)

    const noProviders = Vue.computed(() => {
      const c = catalog.value
      return c.catalog && Object.keys(c.catalog).length === 0
    })

    const providerList = Vue.computed(() => catalog.value.catalog || {})

    const canChange = Vue.computed(() => !store.sessionActive && !store.isBusy)

    function toggle() { if (canChange.value) open.value = !open.value }

    function isActive(name, model) {
      const a = catalog.value.active
      return a && a.provider === name && a.model === model
    }

    async function switchModel(provider, model) {
      switchError.value = null
      try {
        const res = await fetch('/api/switch-provider', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ provider, model })
        })
        if (!res.ok) { const d = await res.json(); throw new Error(d.detail) }
        const data = await res.json()
        catalog.value.active = data.active
        open.value = false
      } catch (e) { switchError.value = e.message }
    }

    Vue.onMounted(async () => {
      try {
        const res = await fetch('/api/providers')
        catalog.value = await res.json()
      } catch (_) {}
    })

    function closeDropdown(e) {
      if (open.value) { const el = e.target.closest('.relative'); if (!el) open.value = false }
    }
    if (typeof document !== 'undefined') document.addEventListener('mousedown', closeDropdown)

    return { store, catalog, open, switchError, noProviders, providerList, canChange, toggle, isActive, switchModel }
  }
}
