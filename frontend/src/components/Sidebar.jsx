function Sidebar({history,mode,setMode}){

return(

<div className="sidebar">

<h2>RAG Assistant</h2>

<div className="mode-switch">
<button
className={mode==="answer" ? "mode-btn active" : "mode-btn"}
onClick={()=>setMode("answer")}
>
Answer
</button>
<button
className={mode==="search" ? "mode-btn active" : "mode-btn"}
onClick={()=>setMode("search")}
>
Search
</button>
</div>

{history.map((h,i)=>(

<div key={i} className="history-item">
{h.slice(0,40)}
</div>

))}

</div>

)

}

export default Sidebar
