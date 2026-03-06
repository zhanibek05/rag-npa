import { useState } from "react"
import axios from "axios"

import ChatMessage from "./components/ChatMessage"
import ChatInput from "./components/ChatInput"
import Sidebar from "./components/Sidebar"

import "./App.css"

const API="http://localhost:8000"

function App(){

const [messages,setMessages]=useState([])
const [query,setQuery]=useState("")
const [loading,setLoading]=useState(false)
const [history,setHistory]=useState([])
const [mode,setMode]=useState("answer")

const sendMessage=async(e)=>{

e.preventDefault()

if(!query.trim())return

const userMsg={
role:"user",
text:query
}

setMessages(prev=>[...prev,userMsg])
setHistory(prev=>[query,...prev])

setLoading(true)

try{

let aiMsg

if(mode==="search"){

const res=await axios.post(`${API}/search`,{
query:query
})

aiMsg={
role:"assistant",
text:`Найдено результатов: ${res.data.length}`,
sources:res.data
}

}else{

const res=await axios.post(`${API}/answer`,{
query:query
})

aiMsg={
role:"assistant",
text:res.data.answer,
sources:res.data.sources
}

}

setMessages(prev=>[...prev,aiMsg])

}catch(err){

console.error(err)

}

setLoading(false)
setQuery("")

}

return(

<div className="app">

<Sidebar history={history} mode={mode} setMode={setMode}/>

<div className="chat-area">

<div className="messages">

{messages.map((m,i)=>(
<ChatMessage key={i} message={m}/>
))}

{loading && (
<ChatMessage message={{role:"assistant",text:"AI думает..."}}/>
)}

</div>

<ChatInput
query={query}
setQuery={setQuery}
onSubmit={sendMessage}
loading={loading}
mode={mode}
/>

</div>

</div>

)

}

export default App
