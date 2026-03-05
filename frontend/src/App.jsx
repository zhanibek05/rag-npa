import { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [mode, setMode] = useState('answer'); // 'answer' or 'search'

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/search`, {
        query: query,
        top_k: 5
      });
      setSearchResults(response.data);
      setAnswer(null);
    } catch (error) {
      console.error('Search error:', error);
      alert('Ошибка поиска: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/answer`, {
        query: query,
        top_k: 10,
        max_context_chars: 7000
      });
      setAnswer(response.data);
      setSearchResults([]);
    } catch (error) {
      console.error('Answer error:', error);
      alert('Ошибка генерации ответа: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (mode === 'search') {
      handleSearch();
    } else {
      handleAnswer();
    }
  };

  return (
    <div className="app">
      <header>
        <h1>🎓 RAG NPA Assistant</h1>
        <p>Помощник по нормативно-правовым актам в сфере образования</p>
      </header>

      <div className="container">
        <form onSubmit={handleSubmit} className="search-form">
          <div className="mode-toggle">
            <button
              type="button"
              className={mode === 'search' ? 'active' : ''}
              onClick={() => setMode('search')}
            >
              🔍 Поиск
            </button>
            <button
              type="button"
              className={mode === 'answer' ? 'active' : ''}
              onClick={() => setMode('answer')}
            >
              💬 Ответ
            </button>
          </div>

          <div className="input-group">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Введите ваш вопрос..."
              disabled={loading}
            />
            <button type="submit" disabled={loading || !query.trim()}>
              {loading ? 'Загрузка...' : mode === 'search' ? 'Искать' : 'Спросить'}
            </button>
          </div>
        </form>

        {answer && (
          <div className="answer-section">
            <h2>Ответ:</h2>
            <div className="answer-text">
              {answer.answer}
            </div>

            <h3>Источники:</h3>
            <div className="sources">
              {answer.sources.map((source, idx) => (
                <div key={source.id} className="source-card">
                  <div className="source-header">
                    <span className="source-number">#{idx + 1}</span>
                    <span className="source-score">
                      Релевантность: {(source.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <p className="source-text">{source.text.slice(0, 300)}...</p>
                  {source.source_url && (
                    <a href={source.source_url} target="_blank" rel="noopener noreferrer">
                      Открыть источник
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {searchResults.length > 0 && (
          <div className="search-results">
            <h2>Результаты поиска:</h2>
            {searchResults.map((result, idx) => (
              <div key={result.id} className="result-card">
                <div className="result-header">
                  <span className="result-number">#{idx + 1}</span>
                  <span className="result-score">
                    Релевантность: {(result.score * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="result-text">{result.text}</p>
                {result.source_url && (
                  <a href={result.source_url} target="_blank" rel="noopener noreferrer">
                    Открыть источник
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
