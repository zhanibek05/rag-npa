import { useEffect, useState } from "react"
import { useSearchParams, useNavigate } from "react-router-dom"
import axios from "axios"

const API = "http://localhost:8000"

export default function VerifyEmail() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const token = params.get("token")
  const [status, setStatus] = useState(token ? "verifying" : "invalid")

  useEffect(() => {
    if (!token) return
    axios
      .get(`${API}/auth/verify?token=${encodeURIComponent(token)}`)
      .then(() => {
        setStatus("success")
        setTimeout(() => navigate("/"), 3000)
      })
      .catch(() => setStatus("invalid"))
  }, [navigate, token])

  return (
    <div className="auth-page">
      <div className="auth-box">
        <h2>RAG Assistant</h2>
        {status === "verifying" && <p className="verify-verifying">Проверяем email...</p>}
        {status === "success" && (
          <p className="verify-success">
            Email подтверждён. Переходим в чат...
          </p>
        )}
        {status === "invalid" && (
          <p className="verify-error">
            Недействительная или устаревшая ссылка подтверждения.
          </p>
        )}
      </div>
    </div>
  )
}
