import { useState } from "react"
import { useNavigate, Navigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

function Auth() {
  const { login, register, user } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState("login")
  const [form, setForm] = useState({ username: "", email: "", password: "" })
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [loading, setLoading] = useState(false)

  if (user) return <Navigate to="/" replace />

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
        setSuccess("Регистрация успешна. Проверьте email, чтобы подтвердить аккаунт.")
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
      <section className="auth-shell" aria-label="Авторизация">
        <div className="auth-showcase" aria-hidden="true">
          <div className="auth-brand-mark">NPA</div>
          <div className="auth-showcase-copy">
            <span className="auth-kicker">Legal intelligence workspace</span>
            <h1>Legal Atlas</h1>
            <p>Войдите в пространство, где нормативные документы собираются в понятные маршруты, ответы и источники.</p>
          </div>
          <div className="auth-visual auth-atlas-visual">
            <div className="auth-atlas-grid"></div>
            <div className="auth-document auth-document-main">
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <strong>Вход</strong>
            </div>
            <div className="auth-document auth-document-back">
              <span></span>
              <span></span>
              <span></span>
              <strong>Доступ</strong>
            </div>
            <div className="auth-document auth-document-side">
              <span></span>
              <span></span>
              <strong>RAG</strong>
            </div>
            <div className="auth-route auth-route-a"></div>
            <div className="auth-route auth-route-b"></div>
            <div className="auth-node auth-node-a"></div>
            <div className="auth-node auth-node-b"></div>
            <div className="auth-node auth-node-c"></div>
            <div className="auth-atlas-index">02</div>
          </div>
          <div className="auth-metrics">
            <div>
              <strong>RAG</strong>
              <span>поиск</span>
            </div>
            <div>
              <strong>AI</strong>
              <span>ответы</span>
            </div>
            <div>
              <strong>DOCS</strong>
              <span>база</span>
            </div>
          </div>
        </div>

        <div className="auth-box">
          <div className="auth-heading">
            <span className="auth-mobile-mark">NPA</span>
            <span className="auth-kicker">Добро пожаловать</span>
            <h2>{tab === "login" ? "Вход в кабинет" : "Создать аккаунт"}</h2>
          </div>

          <div className="auth-tabs" role="tablist" aria-label="Режим авторизации">
            <button
              type="button"
              role="tab"
              aria-selected={tab === "login"}
              className={tab === "login" ? "auth-tab active" : "auth-tab"}
              onClick={() => setTab("login")}
            >
              Войти
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === "register"}
              className={tab === "register" ? "auth-tab active" : "auth-tab"}
              onClick={() => setTab("register")}
            >
              Регистрация
            </button>
          </div>

          <form onSubmit={submit} className="auth-form">
            <label className="auth-field">
              <span>Имя пользователя</span>
              <input
                name="username"
                placeholder="Введите логин"
                value={form.username}
                onChange={handle}
                autoComplete="username"
                required
              />
            </label>
            {tab === "register" && (
              <label className="auth-field">
                <span>Email</span>
                <input
                  name="email"
                  type="email"
                  placeholder="name@example.com"
                  value={form.email}
                  onChange={handle}
                  autoComplete="email"
                  required
                />
              </label>
            )}
            <label className="auth-field">
              <span>Пароль</span>
              <input
                name="password"
                type="password"
                placeholder="Введите пароль"
                value={form.password}
                onChange={handle}
                autoComplete={tab === "login" ? "current-password" : "new-password"}
                required
              />
            </label>
            {error && <div className="auth-error">{error}</div>}
            {success && <div className="auth-success">{success}</div>}
            <button type="submit" className="auth-submit" disabled={loading}>
              <span>
                {loading ? "Подождите..." : tab === "login" ? "Войти" : "Зарегистрироваться"}
              </span>
              <span className="auth-submit-arrow">→</span>
            </button>
          </form>
        </div>
      </section>
    </div>
  )
}

export default Auth
