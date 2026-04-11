import { useEffect, useState } from "react"
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

  const headers = { Authorization: `Bearer ${token}` }

  useEffect(() => {
    axios.get(`${API}/admin/users`, { headers }).then((r) => setUsers(r.data))
    axios.get(`${API}/admin/stats`, { headers }).then((r) => setStats(r.data))
  }, [])

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
        <h3 className="admin-sidebar-title">Admin Panel</h3>
        <button className="admin-back-btn" onClick={() => navigate("/")}>
          ← Назад в чат
        </button>
      </div>

      <div className="admin-content">
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

        <h2 className="admin-section-title" style={{ marginTop: "32px" }}>Пользователи</h2>
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
                <td>{u.is_verified ? "✅" : "❌"}</td>
                <td>{u.is_active ? "✅" : "❌"}</td>
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
  )
}
