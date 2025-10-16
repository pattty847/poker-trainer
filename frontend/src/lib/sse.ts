export function backoffNext() {
  // Simple capped backoff
  const now = Date.now()
  const slot = now % 5000
  return 300 + (slot % 4700)
}

export function subscribe(url: string, onEvent: (e: any) => void, opts?: { reconnect?: boolean }): EventSource {
  const reconnect = opts?.reconnect !== false
  const es = new EventSource(url)
  es.onmessage = (ev) => onEvent(JSON.parse(ev.data))
  es.onerror = () => {
    if (!reconnect) return
    es.close()
    setTimeout(() => subscribe(url, onEvent, opts), backoffNext())
  }
  return es
}

export function subscribeReason(sessionId: string, archetype: string, onEvt: (e: any) => void, opts?: { reconnect?: boolean }) {
  const url = `/api/reason/stream?sessionId=${encodeURIComponent(sessionId)}&archetype=${encodeURIComponent(archetype)}`
  return subscribe(url, onEvt, opts)
}


