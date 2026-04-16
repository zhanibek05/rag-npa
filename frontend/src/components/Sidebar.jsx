import { useNavigate, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

function Sidebar({ sessions, history = [], onSelectSession, onNewChat, onDeleteSession, currentSessionId }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const isDocsPage = location.pathname === "/documents"
  const sessionItems = sessions || history.map((title, index) => ({ id: `history-${index}`, title }))

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <div className="sidebar-logo">NPA</div>
          <div>
            <h2>RAG Assistant</h2>
            <span>Legal AI</span>
          </div>
        </div>
        {user && (
          <div className="user-info">
            <div className="user-avatar">{user.username?.slice(0, 1).toUpperCase()}</div>
            <div>
              <span className="username">{user.username}</span>
              <span className="user-role">{user.role || "user"}</span>
            </div>
            <button className="logout-btn" onClick={logout}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <path d="M16 17l5-5-5-5"/>
                <path d="M21 12H9"/>
              </svg>
            </button>
          </div>
        )}
      </div>

      <div className="nav-tabs">
        <button
          className={`nav-tab${!isDocsPage ? " active" : ""}`}
          onClick={() => navigate("/")}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/>
          </svg>
          Чат
        </button>
        <button
          className={`nav-tab${isDocsPage ? " active" : ""}`}
          onClick={() => navigate("/documents")}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <path d="M14 2v6h6"/>
            <path d="M16 13H8M16 17H8M10 9H8"/>
          </svg>
          Документы
        </button>
      </div>

      {!isDocsPage && (
        <>
          <button className="new-chat-btn" onClick={onNewChat}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 5v14M5 12h14"/>
            </svg>
            Новый чат
          </button>

          <div className="sessions-list">
            {sessionItems.length > 0 ? (
              sessionItems.map((s) => (
                <div
                  key={s.id}
                  className={`history-item${s.id === currentSessionId ? " active" : ""}`}
                  onClick={() => onSelectSession?.(s.id)}
                >
                  <span className="history-title">{(s.title || "Без названия").slice(0, 36)}</span>
                  <button
                    className="delete-session-btn"
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteSession?.(s.id)
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
              <div className="empty-sessions">
                <span>История чатов пуста</span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default Sidebar
