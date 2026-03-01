import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  user_id: number
  email: string
  full_name: string | null
  role: 'super_admin' | 'tenant_admin' | 'admin' | 'operator' | 'viewer'
  is_active: boolean
  tenant_id: number | null
}

interface AuthState {
  token: string | null
  user: User | null
  activeTenantId: number | null
  activeTenantName: string | null
  setAuth: (token: string, user: User) => void
  logout: () => void
  isAuthenticated: () => boolean
  isSuperAdmin: () => boolean
  isGlobalSuperAdmin: () => boolean
  isAdmin: () => boolean
  switchTenant: (tenantId: number, tenantName: string, token: string) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      activeTenantId: null,
      activeTenantName: null,
      setAuth: (token: string, user: User) => set({
        token,
        user,
        activeTenantId: user.tenant_id,
        activeTenantName: null,
      }),
      logout: () => set({
        token: null,
        user: null,
        activeTenantId: null,
        activeTenantName: null,
      }),
      isAuthenticated: () => !!get().token,
      isSuperAdmin: () => get().user?.role === 'super_admin',
      isGlobalSuperAdmin: () => {
        const state = get()
        return state.user?.role === 'super_admin' && state.user?.tenant_id === 1
      },
      isAdmin: () => {
        const role = get().user?.role
        return role === 'super_admin' || role === 'tenant_admin' || role === 'admin'
      },
      switchTenant: (tenantId: number, tenantName: string, token: string) => set({
        token,
        activeTenantId: tenantId,
        activeTenantName: tenantName,
      }),
    }),
    {
      name: 'auth-storage',
    }
  )
)
