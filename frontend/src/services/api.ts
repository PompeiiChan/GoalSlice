import axios from 'axios'
import { getStoredSessionId } from '@/utils/session'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})

api.interceptors.request.use((config) => {
  const sessionId = getStoredSessionId()
  if (sessionId) {
    config.headers['X-Session-Id'] = sessionId
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      (error.response?.data as { message?: string } | undefined)?.message ||
      error.message ||
      '请求失败'
    return Promise.reject(new Error(message))
  },
)

export default api
