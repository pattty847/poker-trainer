import { useEffect } from 'react'
import { useStore } from './lib/store'
import { subscribeReason } from './lib/sse'
import { applyAction, createSession, getState, resetGame } from './lib/api'

export default function App() {
  const sessionId = useStore((s) => s.sessionId)
  const reasoning = useStore((s) => s.reasoning)
  const gameState = useStore((s) => s.gameState)
  const resetReasoning = useStore((s) => s.resetReasoning)
  const appendReasoning = useStore((s) => s.appendReasoning)

  useEffect(() => {
    if (!sessionId) return
    resetReasoning('beginner')
    const es = subscribeReason(sessionId, 'math_nerd', (e) => {
      if (e.type === 'tag') resetReasoning(e.content)
      if (e.type === 'token') appendReasoning(e.content)
    }, { reconnect: false })
    return () => es.close()
  }, [sessionId])

  return (
    <div>
      <h1>Poker Trainer MVP</h1>
      <button onClick={async () => {
        const r = await createSession()
        useStore.getState().setSession(r.sessionId)
        useStore.getState().setGameState(r.state)
      }}>New Session</button>
      <button onClick={async () => {
        const sid = useStore.getState().sessionId
        if (!sid) return
        const street = useStore.getState().gameState?.street
        const action = street === 'preflop' ? 'call' : 'check'
        const r = await applyAction(sid, action)
        useStore.getState().setGameState(r.state)
      }}>{gameState?.street === 'preflop' ? 'Call (to see flop)' : 'Check (exercise villain)'}</button>
      <div style={{ marginTop: 8 }}>
        <small>Recommended bet size (action.min): {useStore((s) => s.gameState)?.action?.min ?? '-'}</small>
      </div>
      <div style={{ marginTop: 4 }}>
        <small>Board features: {JSON.stringify(useStore((s) => s.gameState)?.metadata?.boardFeatures ?? {})}</small>
      </div>
      <div style={{ marginTop: 8 }}>
        <small>Hero: {JSON.stringify(useStore((s) => s.gameState)?.hero ?? {})}</small>
      </div>
      <div style={{ marginTop: 4 }}>
        <small>Board: {JSON.stringify(useStore((s) => s.gameState)?.board ?? [])}</small>
      </div>
      <div style={{ border: '1px solid #ccc', padding: 12, minHeight: 80, marginTop: 8 }}>{reasoning}</div>
      {gameState?.street === 'showdown' && (
        <div style={{ marginTop: 12, padding: 8, border: '1px dashed #999' }}>
          <strong>Showdown:</strong>
          <div>
            {(() => {
              const hist = (gameState?.history || []) as any[]
              const res = [...hist].reverse().find((h) => h.actor === 'result')
              if (!res) return 'No result found.'
              return `Winner: ${res.winner} | Hero: ${res.heroBest?.category} | Villain: ${res.villainBest?.category} | Pot: ${res.pot}`
            })()}
          </div>
          <div style={{ marginTop: 8 }}>
            <button onClick={async () => {
              const sid = useStore.getState().sessionId
              if (!sid) return
              const r = await resetGame(sid)
              useStore.getState().setGameState(r.state)
            }}>Next Hand</button>
          </div>
        </div>
      )}
    </div>
  )
}


