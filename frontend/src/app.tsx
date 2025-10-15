import { useEffect } from 'react'
import { useStore } from './lib/store'
import { subscribeReason } from './lib/sse'
import { createSession } from './lib/api'

export default function App() {
  const sessionId = useStore((s) => s.sessionId)
  const reasoning = useStore((s) => s.reasoning)
  const resetReasoning = useStore((s) => s.resetReasoning)
  const appendReasoning = useStore((s) => s.appendReasoning)

  useEffect(() => {
    if (!sessionId) return
    resetReasoning('beginner')
    const es = subscribeReason(sessionId, 'math_nerd', (e) => {
      if (e.type === 'tag') resetReasoning(e.content)
      if (e.type === 'token') appendReasoning(e.content)
    })
    return () => es.close()
  }, [sessionId])

  return (
    <div>
      <h1>Poker Trainer MVP</h1>
      <button onClick={async () => {
        const r = await createSession()
        useStore.getState().setSession(r.sessionId)
      }}>New Session</button>
      <div style={{ border: '1px solid #ccc', padding: 12, minHeight: 80 }}>{reasoning}</div>
    </div>
  )
}


