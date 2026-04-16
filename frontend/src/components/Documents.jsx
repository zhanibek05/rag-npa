import { useState, useEffect, useRef } from "react"
import axios from "axios"
import { useAuth } from "../context/AuthContext"

const API = "http://localhost:8000"

function Documents() {
  const { token } = useAuth()
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
    } catch (err) {
      console.error(err)
    }
    setLoading(false)
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
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
    } catch (err) {
      console.error(err)
    }
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="docs-page">
      <div className="docs-header">
        <div>
          <span className="workspace-kicker">Document vault</span>
          <h2>База документов</h2>
        </div>
        <span className="docs-count">{total} документов</span>
      </div>

      <form className="upload-form" onSubmit={handleUpload}>
        <div className="upload-form-title">
          <span>Добавить документ</span>
          <small>.docx .pdf .txt</small>
        </div>
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
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <path d="M17 8l-5-5-5 5"/>
              <path d="M12 3v12"/>
            </svg>
            <span>{file ? file.name : "Выбрать файл"}</span>
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
          <div className="table-shell">
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
          </div>

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
