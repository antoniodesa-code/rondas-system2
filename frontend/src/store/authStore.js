import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      tecnico: null,
      setAuth: (token, tecnico) => set({ token, tecnico }),
      logout: () => set({ token: null, tecnico: null }),
    }),
    { name: 'ronda-auth' }
  )
)
