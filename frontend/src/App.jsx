import { useState } from "react"
import { Routes, Route, Navigate } from "react-router-dom"

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

    setMessages(prev => [...prev, { role: "user", text }])
    setHistory(prev => [text, ...prev])
    setQuery("")
    setLoading(true)

    setMessages(prev => [...prev, { role: "assistant", text: "", sources: [], suggestions: [] }])

    try {
      const response = await fetch(`${API}/answer/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text }),
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          const data = JSON.parse(line.slice(6))

          if (data.type === "sources") {
            setMessages(prev => {
              const updated = [...prev]
              updated[updated.length - 1] = { ...updated[updated.length - 1], sources: data.sources }
              return updated
            })
          } else if (data.type === "token") {
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[updated.length - 1]
              updated[updated.length - 1] = { ...last, text: last.text + data.text }
              return updated
            })
          } else if (data.type === "suggestions") {
            setMessages(prev => {
              const updated = [...prev]
              updated[updated.length - 1] = { ...updated[updated.length - 1], suggestions: data.suggestions }
              return updated
            })
          }
        }
      }
    } catch (err) {
      console.error(err)
    }

    setLoading(false)
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
