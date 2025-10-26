import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Loader, Bot, User } from 'lucide-react'
import { api } from '../services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hi! I\'m your BU Course Planning assistant. I can help you navigate the website and answer questions about:\n\n📚 Finding and searching courses\n📅 Planning your semesters\n🎯 Getting career recommendations\n👨🏫 Researching professors\n\nWhat would you like help with?'
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage: Message = {
      role: 'user',
      content: inputMessage
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await api.post('/api/chatbot/', {
        message: inputMessage,
        history: messages
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.response || 'I received your message but had trouble generating a response. Could you rephrase your question?'
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error: any) {
      console.error('Chatbot error:', error)
      
      let errorContent = "I'm having trouble connecting right now. But I can still help you navigate! Ask me about finding courses, planning semesters, career recommendations, or researching professors."
      
      // Check if it's a network error
      if (!error.response) {
        errorContent = "I couldn't connect to the server. Please check your internet connection and try again."
      } else if (error.response?.status === 503) {
        errorContent = "The AI service is temporarily unavailable. But I can still help you navigate the website! Ask me about the Explorer, Planner, Progress, or Professors pages."
      } else if (error.response?.status === 500) {
        errorContent = "I encountered an error processing your request. Could you try rephrasing your question? I can help with finding courses, planning semesters, or navigating the site."
      }

      const errorMessage: Message = {
        role: 'assistant',
        content: errorContent
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-16 h-16 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-full shadow-2xl hover:shadow-3xl transition-all duration-300 flex items-center justify-center group hover:scale-110 z-50"
          aria-label="Open chatbot"
        >
          <MessageCircle size={28} className="group-hover:scale-110 transition-transform" />
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white animate-pulse"></span>
        </button>
      )}

      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-white rounded-2xl shadow-2xl flex flex-col z-50 border-2 border-gray-200">
          <div className="bg-gradient-to-r from-red-600 to-red-700 text-white px-6 py-4 rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <Bot size={24} />
              </div>
              <div>
                <h3 className="font-bold text-lg">BU Course Assistant</h3>
                <p className="text-xs text-white/80">Always here to help</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="hover:bg-white/20 p-2 rounded-lg transition-colors"
              aria-label="Close chatbot"
            >
              <X size={20} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.role === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-red-600 text-white'
                }`}>
                  {message.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                </div>
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-900 border border-gray-200'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 bg-red-600 text-white rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot size={18} />
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 flex items-center gap-2">
                  <Loader size={16} className="animate-spin text-red-600" />
                  <span className="text-sm text-gray-600">Thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 border-t border-gray-200 bg-white rounded-b-2xl">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about courses..."
                className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-xl focus:border-red-500 focus:ring-2 focus:ring-red-200 outline-none transition-all text-sm"
                disabled={isLoading}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="bg-red-600 hover:bg-red-700 disabled:bg-gray-300 text-white px-4 py-3 rounded-xl transition-all disabled:cursor-not-allowed flex items-center justify-center min-w-[48px]"
                aria-label="Send message"
              >
                <Send size={20} />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Powered by Google Gemini AI
            </p>
          </div>
        </div>
      )}
    </>
  )
}
