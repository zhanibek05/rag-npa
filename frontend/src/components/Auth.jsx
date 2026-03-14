import { useState } from "react"
import { useAuth } from "../context/AuthContext"

function Auth() {
  const { login, register } = useAuth()
  const [tab, setTab] = useState("login")
  const [form, setForm] = useState({ username: "", email: "", password: "" })
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      if (tab === "login") {
        await login(form.username, form.password)
      } else {
        await register(form.username, form.email, form.password)
        await login(form.username, form.password)
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
          <button type="submit" disabled={loading}>
            {loading ? "..." : tab === "login" ? "Войти" : "Зарегистрироваться"}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Auth
