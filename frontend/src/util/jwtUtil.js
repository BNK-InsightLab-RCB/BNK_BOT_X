import axios from 'axios'
import { clearStoredAuth, getStoredAuth, setStoredAuth } from '../stores/authStore.js'
import { refreshRequest } from '../api/authapi/authAPI.js'

const jwtAxios = axios.create({
  baseURL: import.meta.env.VITE_API_HOST || 'http://localhost:8080/api/v1'
})

const beforeReq = (config) => {
  const auth = getStoredAuth()
  if (auth?.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
}

const failReq = (error) => Promise.reject(error)

const beforeRes = async (res) => res

const failRes = async (error) => {
  const originalRequest = error.config
  const auth = getStoredAuth()

  if (error.response?.status === 401 && auth?.refreshToken && !originalRequest?._retry) {
    originalRequest._retry = true
    try {
      const refreshed = await refreshRequest(auth.refreshToken)
      setStoredAuth(refreshed)
      originalRequest.headers.Authorization = `Bearer ${refreshed.accessToken}`
      return await axios(originalRequest)
    } catch (refreshError) {
      clearStoredAuth()
      return Promise.reject(refreshError)
    }
  }

  return Promise.reject(error)
}

jwtAxios.interceptors.request.use(beforeReq, failReq)
jwtAxios.interceptors.response.use(beforeRes, failRes)

export default jwtAxios
