import { defineStore } from 'pinia'

const AUTH_KEY = 'bnk_bot_x_auth'

function readAuth() {
  const raw = localStorage.getItem(AUTH_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    auth: readAuth()
  }),
  getters: {
    isLogin: (state) => !!state.auth?.accessToken,
    isAdmin: (state) => state.auth?.role === 'ADMIN',
    userName: (state) => state.auth?.name || state.auth?.loginId || ''
  },
  actions: {
    setAuth(auth) {
      this.auth = auth
      localStorage.setItem(AUTH_KEY, JSON.stringify(auth))
    },
    clearAuth() {
      this.auth = null
      localStorage.removeItem(AUTH_KEY)
    }
  }
})

export function getStoredAuth() {
  return readAuth()
}

export function setStoredAuth(auth) {
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth))
}

export function clearStoredAuth() {
  localStorage.removeItem(AUTH_KEY)
}
