const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export async function httpRequest<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const isFormData = init?.body instanceof FormData

  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      ...(!isFormData ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  })

  if (!res.ok) {
    const body = await res.text()
    throw new Error(`HTTP ${res.status}: ${body}`)
  }

  if (res.status === 204) return undefined as unknown as T
  return res.json() as Promise<T>
}
