export interface User {
  id: number
  firstName: string
  lastName: string
  email: string
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// FastAPI returns { detail: string } for our errors and
// { detail: [{ loc, msg }] } for validation errors.
function errorMessage(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { loc?: string[]; msg?: string }
    const field = first.loc?.[first.loc.length - 1]?.replace('_', ' ')
    const msg = first.msg?.replace(/^Value error, /, '') ?? 'is invalid'
    return field ? `${field[0].toUpperCase()}${field.slice(1)}: ${msg}` : msg
  }
  return 'Something went wrong. Please try again.'
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api/auth${path}`, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new ApiError(res.status, errorMessage(data.detail))
  return data as T
}

export const authApi = {
  register: (body: { first_name: string; last_name: string; email: string; password: string }) =>
    request<{ message: string }>('/register', { method: 'POST', body: JSON.stringify(body) }),
  login: (email: string, password: string) =>
    request<{ user: User }>('/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  logout: () => request<{ message: string }>('/logout', { method: 'POST' }),
  me: () => request<{ user: User }>('/me'),
  verifyEmail: (token: string) =>
    request<{ message: string }>('/verify-email', { method: 'POST', body: JSON.stringify({ token }) }),
  resendVerification: (email: string) =>
    request<{ message: string }>('/resend-verification', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
}
