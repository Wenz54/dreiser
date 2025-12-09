import { useState, useEffect, useRef } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Paper,
  CircularProgress,
} from '@mui/material'
import { Send as SendIcon } from '@mui/icons-material'
import { toast } from 'react-toastify'
import api from '../services/api'

interface Message {
  id: string
  role: string
  content: string
  created_at: string
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<null | HTMLDivElement>(null)

  useEffect(() => {
    fetchHistory()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const fetchHistory = async () => {
    try {
      const response = await api.get('/chat/history')
      setMessages(response.data.messages || [])
    } catch (error) {
      console.error('Failed to fetch chat history:', error)
    }
  }

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage = input
    setInput('')
    setLoading(true)

    // Add user message immediately
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: 'user',
        content: userMessage,
        created_at: new Date().toISOString(),
      },
    ])

    try {
      const response = await api.post('/chat/message', {
        message: userMessage,
      })

      // Add assistant response
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.data.response,
          created_at: new Date().toISOString(),
        },
      ])
    } catch (error) {
      console.error('Chat message failed:', error)
      toast.error('Failed to get response from AI assistant')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        AI Trading Assistant
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        GPT-4 powered assistant to help you understand your trading results
      </Typography>

      <Card sx={{ mt: 3, height: '70vh', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flex: 1, overflow: 'auto' }}>
          {messages.length === 0 ? (
            <Box sx={{ textAlign: 'center', mt: 4 }}>
              <Typography variant="h6" color="text.secondary">
                Start a conversation with your AI assistant
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Ask about your portfolio, trading results, or get market insights
              </Typography>
            </Box>
          ) : (
            <Box>
              {messages.map((message) => (
                <Paper
                  key={message.id}
                  sx={{
                    p: 2,
                    mb: 2,
                    bgcolor: message.role === 'user' ? 'primary.dark' : 'background.paper',
                    maxWidth: '80%',
                    ml: message.role === 'user' ? 'auto' : 0,
                  }}
                >
                  <Typography variant="caption" color="text.secondary">
                    {message.role === 'user' ? 'You' : 'AI Assistant'}
                  </Typography>
                  <Typography variant="body1" sx={{ mt: 0.5, whiteSpace: 'pre-wrap' }}>
                    {message.content}
                  </Typography>
                </Paper>
              ))}
              {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              )}
              <div ref={messagesEndRef} />
            </Box>
          )}
        </CardContent>
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              placeholder="Ask me anything about your trading..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !loading && handleSend()}
              disabled={loading}
            />
            <Button
              variant="contained"
              onClick={handleSend}
              disabled={loading || !input.trim()}
              endIcon={<SendIcon />}
            >
              Send
            </Button>
          </Box>
        </Box>
      </Card>
    </Box>
  )
}







