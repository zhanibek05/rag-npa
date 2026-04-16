import { useState, useEffect, useCallback } from "react"
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

function ChatApp() {
  const { token } = useAuth()
  const [messages, setMessages] = useState([])
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState("answer")
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)

  const authHeaders = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }

  const loadSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API}/chat/sessions`, { headers: authHeaders })
      if (res.ok) {
        const data = await res.json()
        setSessions(data)
      }
    } catch (err) {
      console.error("Ошибка загрузки сессий:", err)
    }
  }, [token])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  const selectSession = async (sessionId) => {
    try {
      const res = await fetch(`${API}/chat/sessions/${sessionId}`, { headers: authHeaders })
      if (res.ok) {
        const data = await res.json()
        setMessages(data.messages.map(m => ({ role: m.role, text: m.text, sources: m.sources || [] })))
        setCurrentSessionId(sessionId)
      }
    } catch (err) {
      console.error("Ошибка загрузки сессии:", err)
    }
  }

  const startNewChat = () => {
    setMessages([])
    setQuery("")
    setLoading(false)
    setCurrentSessionId(null)
  }

  const deleteSession = async (sessionId) => {
    try {
      const res = await fetch(`${API}/chat/sessions/${sessionId}`, {
        method: "DELETE",
        headers: authHeaders,
      })
      if (res.ok) {
        setSessions(prev => prev.filter(s => s.id !== sessionId))
        if (currentSessionId === sessionId) {
          startNewChat()
        }
      }
    } catch (err) {
      console.error("Ошибка удаления сессии:", err)
    }
  }

  const sendSuggestion = (text) => {
    sendMessage(null, text)
  }

  const sendMessage = async (e, suggestedQuery) => {
    e?.preventDefault()
    const text = suggestedQuery ?? query
    if (!text.trim()) return

    setQuery("")
    setLoading(true)

    // Создаём сессию если её нет
    let sessionId = currentSessionId
    if (!sessionId) {
      try {
        const res = await fetch(`${API}/chat/sessions`, {
          method: "POST",
          headers: authHeaders,
          body: JSON.stringify({ title: text.slice(0, 60) }),
        })
        if (res.ok) {
          const session = await res.json()
          sessionId = session.id
          setCurrentSessionId(sessionId)
          setSessions(prev => [session, ...prev])
        }
      } catch (err) {
        console.error("Ошибка создания сессии:", err)
      }
    }

    // Добавляем сообщение пользователя в UI
    setMessages(prev => [...prev, { role: "user", text }])

    // Сохраняем сообщение пользователя в БД
    if (sessionId) {
      fetch(`${API}/chat/messages`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ session_id: sessionId, role: "user", text }),
      }).catch(err => console.error("Ошибка сохранения сообщения:", err))
    }

    // Добавляем пустой placeholder для ответа ассистента
    setMessages(prev => [...prev, { role: "assistant", text: "", sources: [], suggestions: [] }])

    let finalText = ""
    let finalSources = []

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
            finalSources = data.sources
            setMessages(prev => {
              const updated = [...prev]
              updated[updated.length - 1] = { ...updated[updated.length - 1], sources: data.sources }
              return updated
            })
          } else if (data.type === "token") {
            finalText += data.text
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

    // Сохраняем ответ ассистента в БД
    if (sessionId && finalText) {
      fetch(`${API}/chat/messages`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ session_id: sessionId, role: "assistant", text: finalText, sources: finalSources }),
      }).catch(err => console.error("Ошибка сохранения ответа:", err))
    }

    setLoading(false)
  }

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        onSelectSession={selectSession}
        onNewChat={startNewChat}
        onDeleteSession={deleteSession}
        currentSessionId={currentSessionId}
      />
      <div className="chat-area">
        <header className="chat-topbar">
          <div>
            <span className="workspace-kicker">AI Legal Workspace</span>
            <h1>RAG Assistant</h1>
          </div>
          <div className="chat-status">
            <span></span>
            Online
          </div>
        </header>
        <div className="messages">
          {messages.length === 0 && (
            <section className="chat-welcome">
              <div className="welcome-copy">
                <div className="welcome-mark">NPA</div>
                <span className="workspace-kicker">Готов к анализу</span>
                <h2>Откройте карту нормативных смыслов</h2>
                <p>Вопрос превращается в маршрут: ассистент проходит по базе документов, находит опорные нормы и собирает ответ с источниками.</p>
              </div>
              <div className="legal-atlas" aria-hidden="true">
                <div className="atlas-grid"></div>
                <div className="atlas-card atlas-card-main">
                  <span></span>
                  <span></span>
                  <span></span>
                  <strong>НПА</strong>
                </div>
                <div className="atlas-card atlas-card-left">
                  <span></span>
                  <span></span>
                  <strong>Поиск</strong>
                </div>
                <div className="atlas-card atlas-card-right">
                  <span></span>
                  <span></span>
                  <strong>Ответ</strong>
                </div>
                <div className="atlas-route atlas-route-a"></div>
                <div className="atlas-route atlas-route-b"></div>
                <div className="atlas-index">01</div>
              </div>
              <div className="welcome-prompts">
                {[
                  "Построй ответ по трудовому договору",
                  "Найди нормы по госзакупкам",
                  "Собери сравнение по лицензированию",
                ].map((text) => (
                  <button
                    key={text}
                    type="button"
                    onClick={() => sendSuggestion(text)}
                  >
                    {text}
                  </button>
                ))}
              </div>
            </section>
          )}
          <div className="messages-stack">
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
  )
}

function App() {
  return (
    <Routes>
      <Route path="/auth" element={<Auth />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <ChatApp />
          </ProtectedRoute>
        }
      />
      <Route
        path="/documents"
        element={
          <ProtectedRoute>
            <DocumentsPage />
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

function DocumentsPage() {
  const { token } = useAuth()
  const [sessions, setSessions] = useState([])

  useEffect(() => {
    fetch(`${API}/chat/sessions`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : [])
      .then(setSessions)
      .catch(() => {})
  }, [token])

  return (
    <div className="app">
      <Sidebar sessions={sessions} />
      <Documents />
    </div>
  )
}

export default App
