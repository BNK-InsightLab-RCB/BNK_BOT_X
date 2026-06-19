import axios from 'axios'

const host = `${import.meta.env.VITE_API_HOST || 'http://localhost:8080/api/v1'}/auth`

export const login = async (loginRequestDTO) => {
  const res = await axios.post(`${host}/login`, loginRequestDTO)
  return res.data
}

export const refreshRequest = async (refreshToken) => {
  const res = await axios.post(`${host}/refresh`, { refreshToken })
  return res.data
}

export const logout = async (jwtAxios) => {
  const res = await jwtAxios.post('/auth/logout')
  return res.data
}

export const me = async (jwtAxios) => {
  const res = await jwtAxios.get('/auth/me')
  return res.data
}
