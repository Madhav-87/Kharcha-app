const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: options.credentials ?? 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.detail || `API request failed (${response.status})`)
  }

  return payload
}

export function checkApiHealth() {
  return apiRequest('/health/')
}
