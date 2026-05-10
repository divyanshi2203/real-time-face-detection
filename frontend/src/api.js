// Thin fetch wrappers around the Flask API. Kept in one place so components
// don't need to know about the JSON envelope or status-code conventions.

export class ApiError extends Error {
  constructor(code, message, status) {
    super(message)
    this.code = code
    this.status = status
  }
}

async function readError(res) {
  let data = null
  try { data = await res.json() } catch (_) { /* not JSON */ }
  return new ApiError(
    data?.error?.code || 'unknown',
    data?.error?.message || `Request failed (HTTP ${res.status})`,
    res.status,
  )
}

export async function uploadVideo(file) {
  const formData = new FormData()
  formData.append('video', file)
  const res = await fetch('/api/videos', { method: 'POST', body: formData })
  if (!res.ok) throw await readError(res)
  return res.json()
}

export async function getRois(videoId) {
  const res = await fetch(`/api/videos/${videoId}/rois`)
  if (!res.ok) throw await readError(res)
  return res.json()
}

export function videoStreamUrl(videoId) {
  return `/api/videos/${videoId}`
}
