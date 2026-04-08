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
    <div style={{ display: "flex", height: "100vh" }}>
      <div style={{ width: "200px", background: "#1e1e2e", padding: "24px", color: "#fff" }}>
        <h3 style={{ marginBottom: "24px" }}>Admin Panel</h3>
        <button
          onClick={() => navigate("/")}
          style={{ background: "none", border: "none", color: "#ccc", cursor: "pointer", padding: 0 }}
        >
          ← Back to Chat
        </button>
      </div>

      <div style={{ flex: 1, padding: "32px", overflowY: "auto" }}>
        {stats && (
          <div style={{ display: "flex", gap: "24px", marginBottom: "32px" }}>
            {[
              { label: "Users", value: stats.users },
              { label: "Sessions", value: stats.sessions },
              { label: "Messages", value: stats.messages },
            ].map((s) => (
              <div
                key={s.label}
                style={{
                  padding: "16px 24px",
                  background: "#f5f5f5",
                  borderRadius: "8px",
                  minWidth: "120px",
                }}
              >
                <div style={{ fontSize: "28px", fontWeight: "bold" }}>{s.value}</div>
                <div style={{ color: "#666" }}>{s.label}</div>
              </div>
            ))}
          </div>
        )}

        <h2>Upload Document</h2>
        <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "8px" }}>
          <input
            type="file"
            accept=".pdf,.csv,.txt,.docx"
            onChange={(e) => setFile(e.target.files[0])}
          />
          <button onClick={uploadFile} disabled={uploading || !file}>
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </div>
        {uploadMsg && <p style={{ color: uploadMsg.includes("failed") ? "red" : "green" }}>{uploadMsg}</p>}

        <h2 style={{ marginTop: "32px" }}>Users</h2>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              {["Username", "Email", "Role", "Verified", "Active", "Actions"].map((h) => (
                <th
                  key={h}
                  style={{ border: "1px solid #ddd", padding: "10px", textAlign: "left", background: "#f5f5f5" }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td style={{ border: "1px solid #ddd", padding: "10px" }}>{u.username}</td>
                <td style={{ border: "1px solid #ddd", padding: "10px" }}>{u.email}</td>
                <td style={{ border: "1px solid #ddd", padding: "10px" }}>{u.role}</td>
                <td style={{ border: "1px solid #ddd", padding: "10px" }}>{u.is_verified ? "✅" : "❌"}</td>
                <td style={{ border: "1px solid #ddd", padding: "10px" }}>{u.is_active ? "✅" : "❌"}</td>
                <td style={{ border: "1px solid #ddd", padding: "10px" }}>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button onClick={() => updateUser(u.id, { role: u.role === "admin" ? "user" : "admin" })}>
                      {u.role === "admin" ? "Remove Admin" : "Make Admin"}
                    </button>
                    <button onClick={() => updateUser(u.id, { is_active: !u.is_active })}>
                      {u.is_active ? "Deactivate" : "Activate"}
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