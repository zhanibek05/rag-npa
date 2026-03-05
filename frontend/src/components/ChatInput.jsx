function ChatInput({query,setQuery,onSubmit,loading}){

return(

<div className="input-container">

<form className="input-box" onSubmit={onSubmit}>

<input
value={query}
onChange={(e)=>setQuery(e.target.value)}
placeholder="Задайте вопрос..."
/>

<button disabled={loading}>
{loading ? "..." : "Send"}
</button>

</form>

</div>

)

}

export default ChatInput