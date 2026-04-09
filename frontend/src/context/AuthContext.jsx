import { createContext, useContext, useEffect, useState } from "react"
import axios from "axios"

const API = "http://localhost:8000"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem("token"))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      axios
        .get(`${API}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem("token")
          setToken(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token])

  const login = async (username, password) => {
    const params = new URLSearchParams()
    params.append("username", username)
    params.append("password", password)
    const res = await axios.post(`${API}/auth/login`, params)
    const t = res.data.access_token
    localStorage.setItem("token", t)
    setToken(t)
    const me = await axios.get(`${API}/auth/me`, {
      headers: { Authorization: `Bearer ${t}` },
    })
    setUser(me.data)
    return me.data
  }

  const register = async (username, email, password) => {
    const res = await axios.post(`${API}/auth/register`, { username, email, password })
    return res.data
  }

  const logout = () => {
    localStorage.removeItem("token")
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, register, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
