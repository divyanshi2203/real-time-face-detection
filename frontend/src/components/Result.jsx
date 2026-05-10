import { videoStreamUrl } from '../api.js'

export default function Result({ video, rois }) {
  const framesWithFace = rois.rois.length
  const totalFrames = rois.frame_count ?? '?'
  const fps = video.fps != null ? video.fps.toFixed(1) : '—'
  const dims = video.width && video.height
    ? `${video.width}×${video.height}`
    : '—'

  return (
    <section className="result">
      <h2>Result</h2>

      <ul className="result-meta">
        <li><span className="muted">Original</span> <code>{video.original_filename}</code></li>
        <li><span className="muted">Resolution</span> {dims}</li>
        <li><span className="muted">FPS</span> {fps}</li>
        <li><span className="muted">Frames with face</span> {framesWithFace} / {totalFrames}</li>
      </ul>

      <video
        className="processed-video"
        src={videoStreamUrl(video.id)}
        controls
        playsInline
      />

      <details open>
        <summary>ROI per frame ({framesWithFace})</summary>
        <div className="roi-table-wrap">
          <table className="roi-table">
            <thead>
              <tr>
                <th>Frame</th>
                <th>t (ms)</th>
                <th>x</th>
                <th>y</th>
                <th>w</th>
                <th>h</th>
              </tr>
            </thead>
            <tbody>
              {rois.rois.map((r) => (
                <tr key={r.frame}>
                  <td>{r.frame}</td>
                  <td>{r.t_ms}</td>
                  <td>{r.x}</td>
                  <td>{r.y}</td>
                  <td>{r.w}</td>
                  <td>{r.h}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  )
}
