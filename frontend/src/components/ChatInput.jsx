function ChatInput({query,setQuery,onSubmit,loading,mode}){

return(

<div className="input-container">

<form className="input-box" onSubmit={onSubmit}>

<input
value={query}
onChange={(e)=>setQuery(e.target.value)}
placeholder={mode==="search" ? "Введите запрос для поиска..." : "Задайте вопрос..."}
/>

<button disabled={loading}>
{loading ? "..." : "Send"}
</button>

</form>

</div>

)

}

export default ChatInput
