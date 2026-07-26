const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, params = {}) {
  const url = new URL(path, BASE_URL)
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value)
    }
  })

  let response
  try {
    response = await fetch(url.toString())
  } catch (err) {
    throw new ApiError('Could not reach the search backend.', 0)
  }

  if (!response.ok) {
    throw new ApiError(`Request failed (${response.status})`, response.status)
  }
  return response.json()
}

export function search(query, { page = 1, size = 10 } = {}) {
  return request('/search', { q: query, page, size })
}

export function suggest(query) {
  return request('/suggest', { q: query })
}

export function popular(limit = 10) {
  return request('/popular', { limit })
}

export function checkHealth() {
  return request('/health')
}

export { ApiError }
