AgentComponents.QuestionPanel = {
  template: '#question-panel-tmpl',
  props: { questions: Array },
  emits: ['submit'],
  setup(props, { emit }) {
    const currentIndex = Vue.ref(0)
    const answers = Vue.ref([])
    const customMode = Vue.ref([])
    const customVal = Vue.ref('')

    const current = Vue.computed(() => props.questions[currentIndex.value])

    const canSubmit = Vue.computed(() => {
      if (customMode.value[currentIndex.value]) return customVal.value.trim().length > 0
      return answers.value[currentIndex.value] !== undefined
    })

    function selectOption(opt) {
      const idx = currentIndex.value
      answers.value[idx] = opt
      customMode.value[idx] = false
    }

    function toggleCustom() {
      const idx = currentIndex.value
      customMode.value[idx] = !customMode.value[idx]
      if (customMode.value[idx]) { answers.value[idx] = undefined; customVal.value = '' }
    }

    function submit() {
      const idx = currentIndex.value
      if (customMode.value[idx]) answers.value[idx] = customVal.value.trim()
      if (!answers.value[idx]) return
      if (idx < props.questions.length - 1) {
        currentIndex.value++
      } else {
        emit('submit', [...answers.value])
      }
    }

    return { currentIndex, answers, customMode, customVal, current, canSubmit, selectOption, toggleCustom, submit }
  }
}
