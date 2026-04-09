import ReactMarkdown from "react-markdown";

function ChatMessage({ message, onSuggestionClick }) {
  return (
    <div className={`message ${message.role}`}>
      <div className="bubble">
        <ReactMarkdown>{message.text}</ReactMarkdown>

        {message.sources && (
          <div className="sources">
            {message.sources.slice(0, 3).map((s, i) => (
              <div key={i} className="source">
                {s.text.slice(0, 120)}...
                {s.source_url && (
                  <div>
                    <a href={s.source_url} target="_blank">источник</a>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {message.suggestions && message.suggestions.length > 0 && onSuggestionClick && (
          <div className="suggestions">
            <div className="suggestions-label">Возможные вопросы</div>
            <div className="suggestions-chips">
              {message.suggestions.map((s, i) => (
                <button
                  key={i}
                  className="suggestion-chip"
                  onClick={() => onSuggestionClick(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;
