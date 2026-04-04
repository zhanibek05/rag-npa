import { useState, useEffect, useRef } from "react"
import { Routes, Route, useNavigate, useParams } from "react-router-dom"
import axios from "axios"

import { useAuth } from "./context/AuthContext"
import Auth from "./components/Auth"
import ChatMessage from "./components/ChatMessage"
import ChatInput from "./components/ChatInput"
import Sidebar from "./components/Sidebar"
import Documents from "./components/Documents"

import "./App.css"

const API = "http://localhost:8000"

function ChatView() {
  const { user, token } = useAuth()
  const { sessionId: sessionIdParam } = useParams()
  const navigate = useNavigate()

  const [messages, setMessages] = useState([])
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState("answer")
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const messagesEndRef = useRef(null)

  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {}

  // scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  // load sessions list on mount / token change
  useEffect(() => {
    if (token) loadSessions()
  }, [token])

  // load chat when URL param changes
  useEffect(() => {
    if (sessionIdParam && token) {
      if (sessionIdParam !== currentSessionId) {
        loadSession(sessionIdParam)
      }
    } else if (!sessionIdParam) {
      setCurrentSessionId(null)
      setMessages([])
    }
  }, [sessionIdParam, token])

  const loadSessions = async () => {
    try {
      const res = await axios.get(`${API}/chat/sessions`, { headers: authHeaders })
      setSessions(res.data)
    } catch {}
  }

  const loadSession = async (id) => {
    try {
      const res = await axios.get(`${API}/chat/sessions/${id}`, { headers: authHeaders })
      setCurrentSessionId(id)
      setMessages(
        res.data.messages.map((m) => ({ role: m.role, text: m.text, sources: m.sources }))
      )
    } catch {}
  }

  const selectSession = (id) => {
    navigate(`/c/${id}`)
  }

  const newChat = () => {
    navigate("/")
  }

  const deleteSession = async (id) => {
    try {
      await axios.delete(`${API}/chat/sessions/${id}`, { headers: authHeaders })
      setSessions((prev) => prev.filter((s) => s.id !== id))
      if (sessionIdParam === id) {
        navigate("/")
      }
    } catch (err) {
      console.error(err)
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    const userMsg = { role: "user", text: query }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    let sessionId = currentSessionId

    try {
      if (!sessionId && token) {
        const s = await axios.post(
          `${API}/chat/sessions`,
          { title: query.slice(0, 60) },
          { headers: authHeaders }
        )
        sessionId = s.data.id
        setCurrentSessionId(sessionId)
        setSessions((prev) => [s.data, ...prev])
        navigate(`/c/${sessionId}`, { replace: true })
      }

      if (token && sessionId) {
        await axios.post(
          `${API}/chat/messages`,
          { session_id: sessionId, role: "user", text: query },
          { headers: authHeaders }
        )
      }

      let aiMsg
      if (mode === "search") {
        const res = await axios.post(`${API}/search`, { query })
        aiMsg = {
          role: "assistant",
          text: `Найдено результатов: ${res.data.length}`,
          sources: res.data,
        }
      } else {
        const res = await axios.post(`${API}/answer`, { query })
        aiMsg = { role: "assistant", text: res.data.answer, sources: res.data.sources }
      }

      setMessages((prev) => [...prev, aiMsg])

      if (token && sessionId) {
        await axios.post(
          `${API}/chat/messages`,
          { session_id: sessionId, role: "assistant", text: aiMsg.text, sources: aiMsg.sources },
          { headers: authHeaders }
        )
        loadSessions()
      }
    } catch (err) {
      console.error(err)
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Произошла ошибка. Попробуйте ещё раз." },
      ])
    }

    setLoading(false)
    setQuery("")
  }

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        onSelectSession={selectSession}
        onNewChat={newChat}
        onDeleteSession={deleteSession}
        currentSessionId={sessionIdParam || null}
      />
      <div className="chat-area">
        <div className="messages">
          {messages.length === 0 && !loading && (
            <div className="empty-state">
              <p>Задайте вопрос по нормативно-правовым актам</p>
            </div>
          )}
          {messages.map((m, i) => (
            <ChatMessage key={i} message={m} />
          ))}
          {loading && <ChatMessage message={{ role: "assistant", text: "" }} thinking />}
          <div ref={messagesEndRef} />
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

function DocumentsView() {
  const { token } = useAuth()
  const [sessions] = useState([])
  const navigate = useNavigate()
  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        onSelectSession={(id) => navigate(`/c/${id}`)}
        onNewChat={() => navigate("/")}
        onDeleteSession={() => {}}
        currentSessionId={null}
      />
      <div className="chat-area">
        <Documents token={token} />
      </div>
    </div>
  )
}

function App() {
  const { user, loading: authLoading } = useAuth()

  if (authLoading) return <div className="loading-screen">Загрузка...</div>
  if (!user) return <Auth />

  return (
    <Routes>
      <Route path="/" element={<ChatView />} />
      <Route path="/c/:sessionId" element={<ChatView />} />
      <Route path="/documents" element={<DocumentsView />} />
    </Routes>
  )
}

export default App

