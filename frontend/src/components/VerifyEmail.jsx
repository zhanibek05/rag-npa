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
        {status === "verifying" && <p>Verifying your email...</p>}
        {status === "success" && (
          <p style={{ color: "green" }}>
            ✅ Email verified! Redirecting to login...
          </p>
        )}
        {status === "invalid" && (
          <p style={{ color: "red" }}>
            ❌ Invalid or expired verification link.
          </p>
        )}
      </div>
    </div>
  )
}
