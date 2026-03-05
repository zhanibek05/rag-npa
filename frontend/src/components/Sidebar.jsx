function Sidebar({history}){

return(

<div className="sidebar">

<h2>RAG Assistant</h2>

{history.map((h,i)=>(

<div key={i} className="history-item">
{h.slice(0,40)}
</div>

))}

</div>

)

}

export default Sidebar