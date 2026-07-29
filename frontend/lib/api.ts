const API_BASE = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || ''

function getApiUrl(path: string) {
  if (!API_BASE) {
    throw new Error('NEXT_PUBLIC_API_URL is not configured')
  }

  if (path.startsWith('/')) {
    return `${API_BASE}${path}`
  }

  return `${API_BASE}/${path}`
}

function parseJson(text: string) {
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch (error) {
    throw new Error('Invalid JSON response')
  }
}

function buildError(response: Response, data: any) {
  const message = data?.error || data?.message || response.statusText || 'Request failed'
  return new Error(message)
}

export async function apiFetch<T>(path: string, options: RequestInit = {}, timeoutMs = 15000): Promise<T> {
  const url = getApiUrl(path)
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(url, { ...options, signal: controller.signal })
    const text = await response.text()
    const data = parseJson(text)

    if (!response.ok) {
      throw buildError(response, data)
    }

    return data as T
  } catch (error: unknown) {
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new Error('Request timed out')
      }
      throw error
    }
    throw new Error('Unexpected request error')
  } finally {
    window.clearTimeout(timeout)
  }
}

export async function apiGet<T>(path: string, options: RequestInit = {}, timeoutMs = 15000) {
  return apiFetch<T>(path, { method: 'GET', ...options }, timeoutMs)
}

export async function apiPost<T>(path: string, body?: unknown, options: RequestInit = {}, timeoutMs = 15000) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers ?? {}),
  }

  const init: RequestInit = {
    method: 'POST',
    ...options,
    headers,
  }

  if (body !== undefined) {
    init.body = JSON.stringify(body)
  }

  return apiFetch<T>(path, init, timeoutMs)
}
