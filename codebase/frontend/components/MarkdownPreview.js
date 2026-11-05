AgentComponents.MarkdownPreview = {
  template: '#markdown-preview-tmpl',
  props: ['path', 'content'],
  setup(props) {
    const bodyRef = Vue.ref(null)
    const html = Vue.computed(() => renderMarkdown(props.content))

    function onClick(event) {
      handleMarkdownClick(event, bodyRef.value, props.path)
    }

    return { bodyRef, html, onClick }
  },
}
