import { useRef, useState } from 'react'

const ACCEPT = 'video/mp4,video/webm,video/quicktime'

function formatSize(bytes) {
  const mb = bytes / (1024 * 1024)
  return mb < 1 ? `${(bytes / 1024).toFixed(0)} KB` : `${mb.toFixed(1)} MB`
}

export default function UploadForm({ onUpload, isUploading }) {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)

  const pickFile = (f) => { if (f) setFile(f) }

  const onDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    pickFile(e.dataTransfer.files?.[0])
  }

  const onSubmit = (e) => {
    e.preventDefault()
    if (file && !isUploading) onUpload(file)
  }

  return (
    <form className="upload-form" onSubmit={onSubmit}>
      <div
        className={`drop-zone${dragOver ? ' is-over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            inputRef.current?.click()
          }
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          hidden
          onChange={(e) => pickFile(e.target.files?.[0])}
        />
        {file ? (
          <p>
            <strong>{file.name}</strong>
            <span className="muted"> · {formatSize(file.size)}</span>
          </p>
        ) : (
          <p>
            Drag a video here, or click to choose.
            <br />
            <span className="muted">mp4 · webm · mov · 50 MB max</span>
          </p>
        )}
      </div>

      <button type="submit" disabled={!file || isUploading}>
        {isUploading ? 'Processing…' : 'Upload & detect'}
      </button>
    </form>
  )
}
