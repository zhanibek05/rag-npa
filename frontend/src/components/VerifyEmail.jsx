import { useEffect, useState } from "react"
import { useSearchParams, useNavigate } from "react-router-dom"
import axios from "axios"

const API = "http://localhost:8000"

export default function VerifyEmail() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState("verifying")

  useEffect(() => {
    const token = params.get("token")
    if (!token) {
      setStatus("invalid")
      return
    }
    axios
      .get(`${API}/auth/verify?token=${token}`)
      .then(() => {
        setStatus("success")
        setTimeout(() => navigate("/"), 3000)
      })
      .catch(() => setStatus("invalid"))
  }, [])

  return (
    <div className="auth-page">
      <div className="auth-box">
        <h2>RAG Assistant</h2>
        {status === "verifying" && <p className="verify-verifying">Проверяем email...</p>}
        {status === "success" && (
          <p className="verify-success">
            ✅ Email подтверждён! Переходим в чат...
          </p>
        )}
        {status === "invalid" && (
          <p className="verify-error">
            ❌ Недействительная или устаревшая ссылка подтверждения.
          </p>
        )}
      </div>
    </div>
  )
}
