const AgentComponents = {}

const scripts = [
  'components/AgentHeader.js',
  'components/AgentChat.js',
  'components/AgentInput.js',
  'components/QuestionPanel.js',
]
let loaded = 0
scripts.forEach(src => {
  const s = document.createElement('script')
  s.src = src
  s.onload = () => {
    loaded++
    if (loaded === scripts.length) mountApp()
  }
  document.body.appendChild(s)
})

function mountApp() {
  const app = Vue.createApp({
    setup() {
      return { store: AgentStore }
    }
  })
  Object.entries(AgentComponents).forEach(([name, comp]) => app.component(name, comp))
  app.mount('#app')
}
