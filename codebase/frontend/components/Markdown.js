// Shared GFM renderer used by chat bubbles and the Markdown preview.
// Display rules: system_devpt_reports/MARKDOWN_DISPLAY_RULES.md

const MD_EXTERNAL_RE = /^(?:[a-z][a-z0-9+.-]*:|\/\/)/i

function mdEscape(text) {
  return String(text == null ? '' : text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function mdSlug(text) {
  return String(text || '')
    .replace(/<[^>]*>/g, '')
    .replace(/&[#a-z0-9]+;/gi, '')
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
}

// Keeps duplicate headings addressable: `## Usage` twice becomes usage, usage-1.
function mdRenderer() {
  const renderer = new marked.Renderer()
  const used = Object.create(null)

  renderer.heading = function (text, level) {
    let slug = mdSlug(text) || 'section'
    if (used[slug] != null) {
      used[slug] += 1
      slug = slug + '-' + used[slug]
    } else {
      used[slug] = 0
    }
    return `<h${level} id="${mdEscape(slug)}">${text}</h${level}>`
  }

  renderer.listitem = function (text) {
    const cls = /<input[^>]*type=["']checkbox["']/.test(text) ? ' class="task-list-item"' : ''
    return `<li${cls}>${text}</li>\n`
  }

  renderer.code = function (code, infostring) {
    const lang = String(infostring || '').trim().split(/\s+/)[0]
    const safe = /^[\w.+#-]+$/.test(lang) ? lang : ''
    const cls = safe ? ` class="language-${mdEscape(safe)}"` : ''
    const label = safe ? `<span class="md-code-lang">${mdEscape(safe)}</span>` : ''
    return `<div class="md-code-block">${label}<pre><code${cls}>${mdEscape(code)}</code></pre></div>`
  }

  return renderer
}

function renderMarkdown(text) {
  if (!text) return ''
  if (typeof marked === 'undefined' || typeof DOMPurify === 'undefined') return mdEscape(text)
  try {
    const html = marked.parse(String(text), {
      gfm: true,
      breaks: false,
      renderer: mdRenderer(),
    })
    return DOMPurify.sanitize(html, { ADD_ATTR: ['checked', 'disabled', 'rel', 'target', 'type'] })
  } catch (_) {
    return '<pre>' + mdEscape(text) + '</pre>'
  }
}

// Open external links safely; relative links are handled by the hosting view.
if (typeof DOMPurify !== 'undefined' && !window.__mdLinkHook) {
  window.__mdLinkHook = true
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.tagName !== 'A') return
    const href = node.getAttribute('href') || ''
    if (MD_EXTERNAL_RE.test(href)) {
      node.setAttribute('target', '_blank')
      node.setAttribute('rel', 'noopener noreferrer')
    }
  })
}

// Resolve a repository-relative link against the document that contains it.
function resolveMarkdownPath(basePath, href) {
  const clean = String(href || '').split('#')[0].split('?')[0]
  if (!clean) return null
  let decoded = clean
  try { decoded = decodeURIComponent(clean) } catch (_) { return null }
  const base = decoded.startsWith('/') ? '' : String(basePath || '').split('/').slice(0, -1).join('/')
  const parts = []
  for (const seg of (base ? base.split('/') : []).concat(decoded.replace(/^\//, '').split('/'))) {
    if (!seg || seg === '.') continue
    if (seg === '..') {
      if (!parts.length) return null
      parts.pop()
    } else {
      parts.push(seg)
    }
  }
  return parts.length ? parts.join('/') : null
}

function scrollMarkdownAnchor(root, hash) {
  if (!root) return
  let id = String(hash || '').replace(/^#/, '')
  try { id = decodeURIComponent(id) } catch (_) {}
  if (!id) return
  const node = root.querySelector('#' + (window.CSS && CSS.escape ? CSS.escape(id) : id))
  if (node) node.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// Delegated click handler: in-page anchors scroll, relative files open in the
// editor, and external links keep their sanitized target=_blank behaviour.
function handleMarkdownClick(event, root, basePath) {
  const anchor = event.target.closest('a')
  if (!anchor) return
  const href = anchor.getAttribute('href') || ''
  if (!href) return
  if (href.startsWith('#')) {
    event.preventDefault()
    scrollMarkdownAnchor(root, href)
    return
  }
  if (MD_EXTERNAL_RE.test(href)) return
  event.preventDefault()
  const path = resolveMarkdownPath(basePath, href)
  if (path) AgentStore.openFileAt(path, 1)
}
