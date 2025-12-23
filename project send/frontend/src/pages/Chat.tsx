import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router-dom"
import {
  newChat,
  sendMessage,
  getHint,
  getAnswer,
  finishChat,
  listChats,
  loadChat,
  getChats,
} from "../api/chat"
import "../chat.css"

type Message = {
  role: "user" | "assistant"
  content: string
}

type ChatItem = {
  id: string
  title: string | null
  created_at: string
  finished: boolean
}

// ───────── helpers ─────────

function typeMessage(
  text: string,
  onUpdate: (value: string) => void,
  speed = 20
) {
  let i = 0
  const interval = setInterval(() => {
    i++
    onUpdate(text.slice(0, i))
    if (i >= text.length) clearInterval(interval)
  }, speed)
}

// ───────── component ─────────

export default function Chat() {
  const navigate = useNavigate()

  const [chatId, setChatId] = useState<string | null>(null)
  const [chatList, setChatList] = useState<ChatItem[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [chats, setChats] = useState<any[]>([])
  async function loadChats() {
    try {
        const data = await getChats()
        setChats(data)
    } catch (e) {
        console.error("Не удалось загрузить историю чатов")
    }
}

  const startedRef = useRef(false)
  const bottomRef = useRef<HTMLDivElement | null>(null)

  // ───────── effects ─────────

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  useEffect(() => {
    if (startedRef.current) return
    startedRef.current = true
    startNewChat()
    refreshChatList()
  }, [])
  useEffect(() => {
    loadChats()
    }, [])

  // ───────── auth ─────────

  function logout() {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    navigate("/login")
  }

  // ───────── chat list ─────────

  async function refreshChatList() {
    try {
      const list = await listChats()
      setChatList(list)
    } catch {}
  }

  async function openChat(id: string) {
    setChatId(id)
    setLoading(true)
    try {
      const chat = await loadChat(id)
      setMessages(chat.messages ?? [])
    } finally {
      setLoading(false)
    }
  }

  // ───────── new chat ─────────

  async function startNewChat() {
    setError("")
    setLoading(true)
    try {
      const res = await newChat()
      setChatId(res.chat_id)
      setMessages([])
      await refreshChatList()
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Не удалось создать чат")
    } finally {
      setLoading(false)
    }
  }

  // ───────── message helpers ─────────

  function pushUser(text: string) {
    setMessages((prev) => [...prev, { role: "user", content: text }])
  }

  function pushAssistantTyping(text: string) {
    setMessages((prev) => [...prev, { role: "assistant", content: "" }])

    typeMessage(text, (partial) => {
      setMessages((prev) => {
        const copy = [...prev]
        copy[copy.length - 1] = { role: "assistant", content: partial }
        return copy
      })
    })
  }

  // ───────── send user message ─────────

  async function send() {
    if (!chatId || !input || loading) return

    const text = input
    setInput("")
    setError("")
    pushUser(text)

    setLoading(true)
    try {
      const reply = await sendMessage(chatId, text)
      pushAssistantTyping(reply || "(пустой ответ модели)")
    } catch (e: any) {
      setError(e?.message ?? "Ошибка отправки")
    } finally {
      setLoading(false)
    }
  }

  // ───────── actions ─────────

  async function hint() {
    if (!chatId || loading) return
    setError("")
    pushUser("Дай подсказку")
    setLoading(true)
    try {
      const reply = await getHint(chatId)
      pushAssistantTyping(String(reply))
    } finally {
      setLoading(false)
    }
  }

  async function answer() {
    if (!chatId || loading) return
    setError("")
    pushUser("Покажи идеальный ответ")
    setLoading(true)
    try {
      const reply = await getAnswer(chatId)
      pushAssistantTyping(String(reply))
    } finally {
      setLoading(false)
    }
  }

  async function finish() {
    if (!chatId || loading) return
    setError("")
    pushUser("Подведи итоги интервью")
    setLoading(true)
    try {
      const reply = await finishChat(chatId)
      pushAssistantTyping(JSON.stringify(reply, null, 2))
      await refreshChatList()
    } finally {
      setLoading(false)
    }
  }

  // ───────── render ─────────

  return (
    <div className="chat-layout">
      {/* ───── sidebar ───── */}
      <div className="sidebar">
        <button onClick={startNewChat} disabled={loading}>
          + New interview
        </button>

        <div className="chat-history">
          {chatList.map((c) => (
            <div
              key={c.id}
              className={`chat-item ${c.id === chatId ? "active" : ""}`}
              onClick={() => openChat(c.id)}
            >
              <div className="chat-title">
                {c.title || "Новое интервью"}
              </div>
              <div className="chat-meta">
                {c.finished ? "✓ Завершено" : "● В процессе"}
              </div>
            </div>
          ))}
        </div>

        <hr />
        <button onClick={logout}>Logout</button>
      </div>

      {/* ───── chat ───── */}
      <div className="chat">
        <div className="messages">
          {error && (
            <div className="message assistant" style={{ border: "1px solid red" }}>
              {error}
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`message ${m.role}`}>
              {m.content}
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              <em>Печатает…</em>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="input-panel">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Первое сообщение — название вакансии"
            onKeyDown={(e) => e.key === "Enter" && send()}
            disabled={loading}
          />

          <button onClick={send} disabled={loading}>Send</button>
          <button onClick={hint} disabled={loading}>Hint</button>
          <button onClick={answer} disabled={loading}>Answer</button>
          <button onClick={finish} disabled={loading}>Finish</button>
        </div>
      </div>
    </div>
  )
}