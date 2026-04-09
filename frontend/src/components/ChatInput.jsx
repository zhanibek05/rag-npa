function ChatInput({ query, setQuery, onSubmit, loading, mode, setMode }) {
  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      onSubmit(e)
    }
  }

  return (
    <div className="input-container">
      <form className="input-card" onSubmit={onSubmit}>
        <textarea
          className="input-textarea"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            e.target.style.height = "auto"
            e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px"
          }}
          onKeyDown={handleKey}
          placeholder={mode === "search" ? "Введите запрос для поиска..." : "Задайте вопрос..."}
          rows={1}
          disabled={loading}
        />

        <div className="input-toolbar">
          <div className="mode-pills">
            <button
              type="button"
              className={mode === "answer" ? "mode-pill active" : "mode-pill"}
              onClick={() => setMode("answer")}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
              </svg>
              Answer
            </button>
            <button
              type="button"
              className={mode === "search" ? "mode-pill active" : "mode-pill"}
              onClick={() => setMode("search")}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              </svg>
              Search
            </button>
          </div>

          <button
            type="submit"
            className="send-btn"
            disabled={loading || !query.trim()}
          >
            {loading ? (
              <svg className="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 19V5M5 12l7-7 7 7"/>
              </svg>
            )}
          </button>
        </div>
      </form>
      <p className="input-hint">Enter — отправить · Shift+Enter — новая строка</p>
    </div>
  )
}

export default ChatInput
