import { useNavigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

function Sidebar({ sessions, onSelectSession, onNewChat, onDeleteSession, currentSessionId }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const isDocsPage = location.pathname === "/documents"

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>RAG Assistant</h2>
        {user && (
          <div className="user-info">
            <span className="username">{user.username}</span>
            <button className="logout-btn" onClick={logout}>
              Выйти
            </button>
          </div>
        )}
      </div>

      <div className="nav-tabs">
        <button
          className={`nav-tab${!isDocsPage ? " active" : ""}`}
          onClick={() => navigate("/")}
        >
          Чат
        </button>
        <button
          className={`nav-tab${isDocsPage ? " active" : ""}`}
          onClick={() => navigate("/documents")}
        >
          Документы
        </button>
      </div>

      {!isDocsPage && (
        <>
          <button className="new-chat-btn" onClick={onNewChat}>
            + Новый чат
          </button>

          <div className="sessions-list">
            {sessions && sessions.length > 0 ? (
              sessions.map((s) => (
                <div
                  key={s.id}
                  className={`history-item${s.id === currentSessionId ? " active" : ""}`}
                  onClick={() => onSelectSession(s.id)}
                >
                  <span className="history-title">{(s.title || "Без названия").slice(0, 36)}</span>
                  <button
                    className="delete-session-btn"
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteSession(s.id)
                    }}
                    title="Удалить чат"
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
                    </svg>
                  </button>
                </div>
              ))
            ) : (
              <div className="empty-sessions">История чатов пуста</div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default Sidebar
