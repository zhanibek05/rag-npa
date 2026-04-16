import { useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import axios from "axios"
import { useAuth } from "../context/AuthContext"

const API = "http://localhost:8000"

export default function AdminPanel() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [users, setUsers] = useState([])
  const [stats, setStats] = useState(null)
  const [file, setFile] = useState(null)
  const [uploadMsg, setUploadMsg] = useState("")
  const [uploading, setUploading] = useState(false)

  const headers = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token])

  useEffect(() => {
    axios.get(`${API}/admin/users`, { headers }).then((r) => setUsers(r.data))
    axios.get(`${API}/admin/stats`, { headers }).then((r) => setStats(r.data))
  }, [headers])

  const updateUser = async (id, data) => {
    await axios.patch(`${API}/admin/users/${id}`, data, { headers })
    const r = await axios.get(`${API}/admin/users`, { headers })
    setUsers(r.data)
  }

  const uploadFile = async () => {
    if (!file) return
    setUploading(true)
    setUploadMsg("")
    try {
      const form = new FormData()
      form.append("file", file)
      const r = await axios.post(`${API}/admin/upload`, form, { headers })
      setUploadMsg(r.data.message)
    } catch (err) {
      setUploadMsg(err.response?.data?.detail || "Upload failed")
    }
    setUploading(false)
  }

  return (
    <div className="admin-layout">
      <div className="admin-sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">NPA</div>
          <div>
            <h3 className="admin-sidebar-title">Admin Panel</h3>
            <span>Control room</span>
          </div>
        </div>
        <button className="admin-back-btn" onClick={() => navigate("/")}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5"/>
            <path d="M12 19l-7-7 7-7"/>
          </svg>
          Назад в чат
        </button>
      </div>

      <div className="admin-content">
        <div className="admin-hero">
          <span className="workspace-kicker">Platform overview</span>
          <h1>Управление системой</h1>
        </div>

        {stats && (
          <div className="admin-stats">
            {[
              { label: "Пользователи", value: stats.users },
              { label: "Сессии", value: stats.sessions },
              { label: "Сообщения", value: stats.messages },
            ].map((s) => (
              <div key={s.label} className="admin-stat-card">
                <div className="admin-stat-value">{s.value}</div>
                <div className="admin-stat-label">{s.label}</div>
              </div>
            ))}
          </div>
        )}

        <div className="admin-panel-section">
          <h2 className="admin-section-title">Загрузить документ</h2>
          <div className="admin-upload-row">
            <input
              type="file"
              accept=".pdf,.csv,.txt,.docx"
              className="admin-file-input"
              onChange={(e) => setFile(e.target.files[0])}
            />
            <button
              className="admin-upload-btn"
              onClick={uploadFile}
              disabled={uploading || !file}
            >
              {uploading ? "Загрузка..." : "Загрузить"}
            </button>
          </div>
          {uploadMsg && (
            <p className={uploadMsg.toLowerCase().includes("fail") || uploadMsg.toLowerCase().includes("error") ? "admin-msg-error" : "admin-msg-success"}>
              {uploadMsg}
            </p>
          )}
        </div>

        <div className="admin-panel-section">
          <h2 className="admin-section-title">Пользователи</h2>
          <div className="table-shell">
            <table className="admin-table">
              <thead>
                <tr>
                  {["Имя", "Email", "Роль", "Подтверждён", "Активен", "Действия"].map((h) => (
                    <th key={h}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>{u.username}</td>
                    <td>{u.email}</td>
                    <td>
                      <span className={`role-badge ${u.role}`}>{u.role}</span>
                    </td>
                    <td>
                      <span className={`boolean-badge ${u.is_verified ? "yes" : "no"}`}>
                        {u.is_verified ? "Да" : "Нет"}
                      </span>
                    </td>
                    <td>
                      <span className={`boolean-badge ${u.is_active ? "yes" : "no"}`}>
                        {u.is_active ? "Да" : "Нет"}
                      </span>
                    </td>
                    <td>
                      <div className="admin-actions">
                        <button
                          className="admin-action-btn"
                          onClick={() => updateUser(u.id, { role: u.role === "admin" ? "user" : "admin" })}
                        >
                          {u.role === "admin" ? "Снять админа" : "Сделать админом"}
                        </button>
                        <button
                          className={`admin-action-btn ${u.is_active ? "danger" : ""}`}
                          onClick={() => updateUser(u.id, { is_active: !u.is_active })}
                        >
                          {u.is_active ? "Деактивировать" : "Активировать"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
