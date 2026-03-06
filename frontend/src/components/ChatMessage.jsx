import ReactMarkdown from "react-markdown";

function ChatMessage({ message }) {

  return (
    <div className={`message ${message.role}`}>

      <div className="bubble">

        <ReactMarkdown>
          {message.text}
        </ReactMarkdown>

        {message.sources && (

          <div className="sources">

            {message.sources.slice(0,3).map((s,i)=>(

              <div key={i} className="source">

                {s.title && (
                  <div className="source-title">
                    {s.title}
                  </div>
                )}

                {typeof s.score === "number" && (
                  <div className="source-score">
                    score: {s.score.toFixed(3)}
                  </div>
                )}

                {s.text.slice(0,120)}...

                {s.source_url && (
                  <div>
                    <a href={s.source_url} target="_blank">
                      источник
                    </a>
                  </div>
                )}

              </div>

            ))}

          </div>

        )}

      </div>

    </div>
  );

}

export default ChatMessage;
