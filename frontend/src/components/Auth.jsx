import { useState } from "react"
import { useNavigate, Navigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

function Auth() {
  const { login, register, user } = useAuth()
  const navigate = useNavigate()

  if (user) return <Navigate to="/" replace />
  const [tab, setTab] = useState("login")
  const [form, setForm] = useState({ username: "", email: "", password: "" })
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [loading, setLoading] = useState(false)

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError("")
    setSuccess("")
    setLoading(true)
    try {
      if (tab === "login") {
        await login(form.username, form.password)
        navigate("/")
      } else {
        await register(form.username, form.email, form.password)
        setSuccess("Registration successful! Please check your email to verify your account.")
        setTab("login")
        setForm({ username: "", email: "", password: "" })
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Ошибка авторизации")
    }
    setLoading(false)
  }

  return (
    <div className="auth-page">
      <div className="auth-box">
        <h2>RAG Assistant</h2>

        <div className="auth-tabs">
          <button
            className={tab === "login" ? "auth-tab active" : "auth-tab"}
            onClick={() => setTab("login")}
          >
            Войти
          </button>
          <button
            className={tab === "register" ? "auth-tab active" : "auth-tab"}
            onClick={() => setTab("register")}
          >
            Регистрация
          </button>
        </div>

        <form onSubmit={submit} className="auth-form">
          <input
            name="username"
            placeholder="Имя пользователя"
            value={form.username}
            onChange={handle}
            required
          />
          {tab === "register" && (
            <input
              name="email"
              type="email"
              placeholder="Email"
              value={form.email}
              onChange={handle}
              required
            />
          )}
          <input
            name="password"
            type="password"
            placeholder="Пароль"
            value={form.password}
            onChange={handle}
            required
          />
          {error && <div className="auth-error">{error}</div>}
          {success && <div className="auth-success">{success}</div>}
          <button type="submit" disabled={loading}>
            {loading ? "..." : tab === "login" ? "Войти" : "Зарегистрироваться"}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Auth
