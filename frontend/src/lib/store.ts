import { create } from 'zustand'

type GameState = any

type State = {
  sessionId: string
  gameState: GameState | null
  reasoning: string
  skillTag: 'beginner' | 'intermediate' | 'advanced'
  setSession: (id: string) => void
  setGameState: (s: GameState) => void
  resetReasoning: (tag: State['skillTag']) => void
  appendReasoning: (chunk: string) => void
}

export const useStore = create<State>((set) => ({
  sessionId: '',
  gameState: null,
  reasoning: '',
  skillTag: 'beginner',
  setSession: (id) => set({ sessionId: id }),
  setGameState: (s) => set({ gameState: s }),
  resetReasoning: (tag) => set({ reasoning: '', skillTag: tag }),
  appendReasoning: (chunk) => set((st) => ({ reasoning: st.reasoning + chunk })),
}))


