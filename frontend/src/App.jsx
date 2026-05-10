import { useState } from 'react'

import { ApiError, getRois, uploadVideo } from './api.js'
import Result from './components/Result.jsx'
import UploadForm from './components/UploadForm.jsx'

export default function App() {
  const [status, setStatus] = useState('idle') // idle | uploading | done | error
  const [video, setVideo] = useState(null)
  const [rois, setRois] = useState(null)
  const [error, setError] = useState(null)

  const reset = () => {
    setStatus('idle')
    setVideo(null)
    setRois(null)
    setError(null)
  }

  const handleUpload = async (file) => {
    setStatus('uploading')
    setError(null)
    setVideo(null)
    setRois(null)
    try {
      const v = await uploadVideo(file)
      const r = await getRois(v.id)
      setVideo(v)
      setRois(r)
      setStatus('done')
    } catch (e) {
      const msg = e instanceof ApiError
        ? `${e.message} (${e.code}, HTTP ${e.status})`
        : e.message || 'Unexpected error'
      setError(msg)
      setStatus('error')
    }
  }

  return (
    <main>
      <header className="app-header">
        <h1>Real-Time Face Detection</h1>
        <p className="muted">
          Upload a clip — the backend draws an axis-aligned bounding box around the
          (single) face on every frame and returns the annotated video plus per-frame
          ROI data.
        </p>
      </header>

      <UploadForm onUpload={handleUpload} isUploading={status === 'uploading'} />

      {status === 'uploading' && (
        <p className="muted">
          Detection runs frame-by-frame on the server, so this can take a moment for
          longer clips.
        </p>
      )}

      {error && (
        <div className="error-banner" role="alert">
          <strong>Error:</strong> {error}
          <button type="button" className="link-button" onClick={reset}>
            Try again
          </button>
        </div>
      )}

      {video && rois && <Result video={video} rois={rois} />}
    </main>
  )
}
