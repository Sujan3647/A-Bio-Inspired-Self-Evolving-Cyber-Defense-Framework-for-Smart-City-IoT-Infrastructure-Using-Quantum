import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  user_id: string
  email: string
  role: string
  full_name: string
  ministry: string
  permissions: Record<string, unknown>
}

interface AuthState {
  token: string | null
  user: User | null
  login: (token: string, user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      login: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'immunogrid-auth' },
  ),
)
