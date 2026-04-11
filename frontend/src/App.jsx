import { useState } from "react"
import { Routes, Route, Navigate } from "react-router-dom"
import axios from "axios"

import { useAuth } from "./context/AuthContext"
import Auth from "./components/Auth"
import ChatMessage from "./components/ChatMessage"
import ChatInput from "./components/ChatInput"
import Sidebar from "./components/Sidebar"
import VerifyEmail from "./components/VerifyEmail"
import AdminPanel from "./components/AdminPanel"
import Documents from "./components/Documents"

import "./App.css"

const API = "http://localhost:8000"

function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth()

  if (loading) return <div>Загрузка...</div>
  if (!user) return <Navigate to="/auth" replace />
  if (adminOnly && user.role !== "admin") return <Navigate to="/" replace />

  return children
}

function App() {
  const [messages, setMessages] = useState([])
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])
  const [mode, setMode] = useState("answer")

  const sendSuggestion = (text) => {
    sendMessage(null, text)
  }

  const sendMessage = async (e, suggestedQuery) => {
    e?.preventDefault()
    const text = suggestedQuery ?? query
    if (!text.trim()) return

    const userMsg = { role: "user", text }
    setMessages(prev => [...prev, userMsg])
    setHistory(prev => [text, ...prev])
    setLoading(true)

    try {
      const res = await axios.post(`${API}/answer`, { query: text })
      const aiMsg = {
        role: "assistant",
        text: res.data.answer,
        sources: res.data.sources,
        suggestions: res.data.suggestions || [],
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (err) {
      console.error(err)
    }

    setLoading(false)
    setQuery("")
  }

  return (
    <Routes>
      <Route path="/auth" element={<Auth />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <div className="app">
              <Sidebar history={history} />
              <div className="chat-area">
                <div className="messages">
                  {messages.map((m, i) => (
                    <ChatMessage
                      key={i}
                      message={m}
                      onSuggestionClick={!loading ? sendSuggestion : null}
                    />
                  ))}
                  {loading && (
                    <ChatMessage message={{ role: "assistant", text: "AI думает..." }} />
                  )}
                </div>
                <ChatInput
                  query={query}
                  setQuery={setQuery}
                  onSubmit={sendMessage}
                  loading={loading}
                  mode={mode}
                  setMode={setMode}
                />
              </div>
            </div>
          </ProtectedRoute>
        }
      />
      <Route
        path="/documents"
        element={
          <ProtectedRoute>
            <div className="app">
              <Sidebar history={history} />
              <Documents />
            </div>
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute adminOnly>
            <AdminPanel />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App
