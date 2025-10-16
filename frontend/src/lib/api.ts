export async function createSession(params?: {
  smallBlind?: number
  bigBlind?: number
  stack?: number
  seed?: number
}) {
  const res = await fetch('/api/game/new', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ smallBlind: 0.5, bigBlind: 1.0, stack: 100, seed: 42, ...(params || {}) }),
  })
  if (!res.ok) throw new Error('Failed to create session')
  return res.json() as Promise<{ sessionId: string; state: any }>
}

export async function applyAction(sessionId: string, action: string, size?: number) {
  const res = await fetch('/api/game/action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId, action, size }),
  })
  if (!res.ok) throw new Error('Failed to apply action')
  return res.json() as Promise<{ state: any; aiActionApplied: boolean }>
}

export async function getState(sessionId: string) {
  const res = await fetch(`/api/game/state?sessionId=${encodeURIComponent(sessionId)}`)
  if (!res.ok) throw new Error('Failed to get state')
  return res.json() as Promise<{ state: any }>
}

export async function resetGame(sessionId: string, seed?: number) {
  const res = await fetch('/api/game/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId, seed }),
  })
  if (!res.ok) throw new Error('Failed to reset game')
  return res.json() as Promise<{ state: any }>
}


