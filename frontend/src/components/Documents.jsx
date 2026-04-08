import { useState, useEffect, useRef } from "react"
import axios from "axios"

const API = "http://localhost:8000"

function Documents({ token }) {
  const [docs, setDocs] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState("")
  const [title, setTitle] = useState("")
  const [file, setFile] = useState(null)
  const fileRef = useRef()

  const PAGE_SIZE = 20
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {}

  const load = async (p = 1) => {
    setLoading(true)
    try {
      const res = await axios.get(`${API}/documents`, {
        params: { page: p, page_size: PAGE_SIZE },
        headers: authHeaders,
      })
      setDocs(res.data.items)
      setTotal(res.data.total)
      setPage(p)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { load(1) }, [])

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file || !title.trim()) return
    setUploading(true)
    setUploadError("")
    const form = new FormData()
    form.append("title", title.trim())
    form.append("file", file)
    try {
      await axios.post(`${API}/documents/upload`, form, { headers: authHeaders })
      setTitle("")
      setFile(null)
      if (fileRef.current) fileRef.current.value = ""
      load(1)
    } catch (err) {
      setUploadError(err.response?.data?.detail || "Ошибка загрузки")
    }
    setUploading(false)
  }

  const handleDelete = async (id) => {
    if (!confirm("Удалить документ из базы и индекса?")) return
    try {
      await axios.delete(`${API}/documents/${id}`, { headers: authHeaders })
      load(page)
    } catch {}
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="docs-page">
      <div className="docs-header">
        <h2>База документов</h2>
        <span className="docs-count">{total} документов</span>
      </div>

      {/* Upload form */}
      <form className="upload-form" onSubmit={handleUpload}>
        <div className="upload-form-title">Добавить документ</div>
        <div className="upload-row">
          <input
            className="upload-title-input"
            type="text"
            placeholder="Название документа"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
          <label className="file-label">
            <input
              ref={fileRef}
              type="file"
              accept=".docx,.pdf,.txt"
              style={{ display: "none" }}
              onChange={(e) => setFile(e.target.files[0])}
              required
            />
            {file ? file.name : "Выбрать файл (.docx, .pdf, .txt)"}
          </label>
          <button
            className="upload-btn"
            type="submit"
            disabled={uploading || !file || !title.trim()}
          >
            {uploading ? "Загрузка..." : "Загрузить"}
          </button>
        </div>
        {uploadError && <div className="upload-error">{uploadError}</div>}
      </form>

      {/* Documents table */}
      {loading ? (
        <div className="docs-loading">Загрузка...</div>
      ) : (
        <>
          <table className="docs-table">
            <thead>
              <tr>
                <th>Название</th>
                <th>Тип</th>
                <th>Дата</th>
                <th>Источник</th>
                <th>Статус</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id}>
                  <td className="doc-title-cell">
                    {d.url && !d.url.startsWith("custom://") ? (
                      <a href={d.url} target="_blank" rel="noreferrer" className="doc-link">
                        {d.title || d.id}
                      </a>
                    ) : (
                      <span>{d.title || d.id}</span>
                    )}
                  </td>
                  <td className="doc-type-cell">{d.doc_type || "—"}</td>
                  <td className="doc-date-cell">{d.adopted_date || "—"}</td>
                  <td>
                    <span className={`source-badge ${d.source}`}>
                      {d.source === "custom" ? "Свой" : "Адилет"}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${d.index_status}`}>
                      {d.index_status}
                    </span>
                  </td>
                  <td>
                    <button
                      className="doc-delete-btn"
                      onClick={() => handleDelete(d.id)}
                      title="Удалить"
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
                      </svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="docs-pagination">
              <button onClick={() => load(page - 1)} disabled={page === 1}>←</button>
              <span>{page} / {totalPages}</span>
              <button onClick={() => load(page + 1)} disabled={page === totalPages}>→</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default Documents
