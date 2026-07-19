import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { querycopilot, listSessions, getMessages } from '../api/client'
import { Send, Bot, User, Mic, MicOff, AlertCircle } from 'lucide-react'
import Badge from '../components/Badge'

// Web Speech API types
declare global {
  interface Window {
    SpeechRecognition: any
    webkitSpeechRecognition: any
  }
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: any[]
  confidence?: number
  created_at?: string
}

const SUGGESTED_QUESTIONS = [
  'What are the recent maintenance findings on pump P-101?',
  'What does the OEM manual say about mechanical seal failure?',
  'Show me the latest inspection findings for CDU Unit 1',
  'What are the OISD-116 requirements for operating procedures?',
  'When was PSV-201 last certified?',
]

export default function Copilot() {
  const [sessionId, setSessionId] = useState<string | undefined>()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [voiceSupported, setVoiceSupported] = useState(false)
  const recognitionRef = useRef<any>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Check voice support on mount
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    setVoiceSupported(!!SpeechRecognition)
  }, [])

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-IN'
    recognition.continuous = false
    recognition.interimResults = true
    recognition.onstart = () => setIsListening(true)
    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((r: any) => r[0].transcript)
        .join('')
      setInput(transcript)
    }
    recognition.onerror = () => setIsListening(false)
    recognition.onend = () => setIsListening(false)
    recognitionRef.current = recognition
    recognition.start()
  }

  const stopListening = () => {
    recognitionRef.current?.stop()
    setIsListening(false)
  }

  const { data: sessions } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => listSessions().then(r => r.data),
  })

  const mutation = useMutation({
    mutationFn: (query: string) =>
      querycopilot({ query, session_id: sessionId, category_filter: categoryFilter || undefined }).then(r => r.data),
    onSuccess: (data) => {
      setSessionId(data.session_id)
      setMessages(prev => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
          confidence: data.confidence === 'high' ? 0.9 : data.confidence === 'medium' ? 0.6 : 0.3,
        },
      ])
    },
  })

  const sendMessage = (query: string) => {
    if (!query.trim()) return
    setMessages(prev => [...prev, { id: `u-${Date.now()}`, role: 'user', content: query }])
    setInput('')
    mutation.mutate(query)
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, mutation.isPending])

  const confidenceColor = (c?: number) =>
    c === undefined ? '' : c >= 0.8 ? 'text-green-400' : c >= 0.55 ? 'text-yellow-400' : 'text-red-400'

  const confidenceLabel = (c?: number) =>
    c === undefined ? '' : c >= 0.8 ? 'High' : c >= 0.55 ? 'Medium' : 'Low'

  return (
    <div className="flex h-full">
      {/* Sidebar — sessions */}
      <aside className="hidden lg:flex flex-col w-56 bg-gray-900 border-r border-gray-800 shrink-0">
        <div className="px-4 py-3 border-b border-gray-800">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">Sessions</p>
        </div>
        <div className="flex-1 overflow-y-auto py-2 px-2 space-y-1">
          <button
            onClick={() => { setSessionId(undefined); setMessages([]) }}
            className="w-full text-left px-3 py-2 rounded-lg text-xs text-blue-400 hover:bg-gray-800 font-medium"
          >
            + New conversation
          </button>
          {(sessions ?? []).map((s: any) => (
            <button
              key={s.id}
              onClick={() => setSessionId(s.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors truncate ${
                s.id === sessionId ? 'bg-blue-900 text-blue-200' : 'text-gray-400 hover:bg-gray-800'
              }`}
            >
              {s.title}
            </button>
          ))}
        </div>
      </aside>

      {/* Chat area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Top bar */}
        <div className="px-4 py-3 bg-gray-900 border-b border-gray-800 flex items-center gap-3">
          <Bot className="w-5 h-5 text-blue-400" />
          <span className="font-semibold text-white">Expert Knowledge Copilot</span>
          <div className="ml-auto">
            <select
              value={categoryFilter}
              onChange={e => setCategoryFilter(e.target.value)}
              className="text-xs bg-gray-800 border border-gray-700 text-gray-300 rounded-lg px-2 py-1.5"
            >
              <option value="">All categories</option>
              <option value="maintenance">Maintenance</option>
              <option value="operating_procedure">Operating Procedures</option>
              <option value="safety">Safety</option>
              <option value="engineering">Engineering</option>
              <option value="inspection">Inspection</option>
              <option value="regulation">Regulations</option>
            </select>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <Bot className="w-12 h-12 text-blue-500 mb-4" />
              <h2 className="text-white font-semibold text-lg">Industrial Knowledge Copilot</h2>
              <p className="text-gray-400 text-sm mt-2 max-w-sm">
                Ask questions about your plant's documents, equipment history, procedures, and regulations.
              </p>
              <div className="mt-6 grid gap-2 w-full max-w-md">
                {SUGGESTED_QUESTIONS.map(q => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="text-left px-4 py-2.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-300 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map(msg => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'assistant' && (
                <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center shrink-0 mt-1">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              )}
              <div className={`max-w-2xl ${msg.role === 'user' ? 'bg-blue-700 text-white' : 'bg-gray-800 text-gray-200'} rounded-2xl px-4 py-3`}>
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">{msg.content}</pre>

                {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-700 space-y-1.5">
                    <p className="text-xs text-gray-500 font-medium">Sources</p>
                    {msg.sources.map((s: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-gray-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
                        <span className="truncate">{s.filename}</span>
                        <span className="text-gray-600 shrink-0">{Math.round(s.similarity_score * 100)}% match</span>
                      </div>
                    ))}
                    {msg.confidence !== undefined && (
                      <p className={`text-xs font-semibold mt-1 ${confidenceColor(msg.confidence)}`}>
                        Confidence: {confidenceLabel(msg.confidence)}
                      </p>
                    )}
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-7 h-7 rounded-full bg-gray-700 flex items-center justify-center shrink-0 mt-1">
                  <User className="w-4 h-4 text-gray-300" />
                </div>
              )}
            </div>
          ))}

          {mutation.isPending && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-gray-800 rounded-2xl px-4 py-3 flex items-center gap-2">
                <div className="flex gap-1">
                  {[0, 1, 2].map(i => (
                    <span key={i} className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                  ))}
                </div>
                <span className="text-xs text-gray-500">Searching knowledge base...</span>
              </div>
            </div>
          )}

          {mutation.isError && (
            <div className="flex items-center gap-2 text-red-400 text-sm bg-red-950 border border-red-800 rounded-lg px-4 py-2">
              <AlertCircle className="w-4 h-4" />
              Failed to get a response. Check backend connection.
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="px-4 py-3 bg-gray-900 border-t border-gray-800">
          <div className={`flex items-end gap-2 bg-gray-800 rounded-xl px-3 py-2 ${isListening ? 'ring-2 ring-red-500' : ''}`}>
            <textarea
              className="flex-1 bg-transparent text-sm text-gray-200 resize-none outline-none max-h-32 scrollbar-thin placeholder-gray-600"
              placeholder={isListening ? '🎤 Listening...' : 'Ask about equipment, procedures, incidents, regulations...'}
              rows={1}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendMessage(input)
                }
              }}
            />
            {/* Voice button */}
            {voiceSupported && (
              <button
                onClick={isListening ? stopListening : startListening}
                title={isListening ? 'Stop listening' : 'Voice input'}
                className={`p-2 rounded-lg transition-colors ${
                  isListening
                    ? 'bg-red-600 hover:bg-red-500 animate-pulse'
                    : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                {isListening ? <MicOff className="w-4 h-4 text-white" /> : <Mic className="w-4 h-4 text-gray-300" />}
              </button>
            )}
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || mutation.isPending}
              className="p-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-4 h-4 text-white" />
            </button>
          </div>
          <p className="text-xs text-gray-600 mt-1.5 text-center">
            {voiceSupported
              ? 'Answers include citations · Enter to send · 🎤 tap mic for voice'
              : 'Answers include citations · Enter to send · Shift+Enter for new line'}
          </p>
        </div>
      </div>
    </div>
  )
}
