import axios from 'axios'

const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  if (typeof window !== 'undefined' && window.location.hostname.includes('replit')) {
    const domain = window.location.hostname
    return `https://${domain.replace('-5000.', '-8000.')}`
  }
  return 'http://localhost:8000'
}

const API_BASE_URL = getApiBaseUrl()

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

/**
 * Call backend proxy for Google AI Studio / Gemini
 * Expects body: { prompt: string, model?: string }
 * Adds a timeout to prevent hanging requests.
 */
export async function callGemini(payload: { prompt: string; model?: string }) {
  try {
    // 20s timeout for slow backend
    return await api.post('/api/gemini/', payload, { timeout: 20000 })
  } catch (error: any) {
    if (error.code === 'ECONNABORTED') {
      throw new Error('Request timed out. The AI server may be down or unreachable.')
    }
    throw error
  }
}
