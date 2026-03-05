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

const res=await axios.post(`${API}/answer`,{
query:query
})

const aiMsg={
role:"assistant",
text:res.data.answer,
sources:res.data.sources
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

<Sidebar history={history}/>

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
/>

</div>

</div>

)

}

export default App