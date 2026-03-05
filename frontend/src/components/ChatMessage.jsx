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