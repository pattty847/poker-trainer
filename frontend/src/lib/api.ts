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


