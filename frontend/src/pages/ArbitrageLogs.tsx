import { useState, useEffect, useRef } from 'react'
import {
  Box,
  Paper,
  Typography,
  Chip,
  IconButton,
  Stack,
  Switch,
  FormControlLabel,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material'
import {
  PlayArrow,
  Pause,
  Clear,
  Download,
} from '@mui/icons-material'
import dayjs from 'dayjs'

interface LogEntry {
  id: string
  timestamp: number
  level: 'INFO' | 'WARN' | 'ERROR' | 'SUCCESS' | 'OPPORTUNITY'
  message: string
  exchange?: string
  symbol?: string
  data?: any
}

export default function ArbitrageLogs() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isAutoScroll, setIsAutoScroll] = useState(true)
  const [isPaused, setIsPaused] = useState(false)
  const [filter, setFilter] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('ALL')
  const logsEndRef = useRef<HTMLDivElement>(null)
  const logsContainerRef = useRef<HTMLDivElement>(null)
  const [userScrolled, setUserScrolled] = useState(false)

  // WebSocket connection for real-time logs with auto-reconnect
  useEffect(() => {
    let ws: WebSocket | null = null
    let reconnectTimeout: NodeJS.Timeout
    let shouldReconnect = true

    const connect = () => {
      try {
        ws = new WebSocket('ws://localhost:8000/api/v2/engine/logs/stream')
        setIsLoading(false)

        ws.onopen = () => {
          console.log('✅ WebSocket connected to logs stream')
        }

        ws.onmessage = (event) => {
          if (isPaused) return

          try {
            const logEntry: LogEntry = JSON.parse(event.data)
            setLogs((prev) => {
              const newLogs = [...prev, logEntry]
              // Keep last 1000 logs in memory
              if (newLogs.length > 1000) {
                return newLogs.slice(-1000)
              }
              return newLogs
            })
          } catch (e) {
            console.error('Failed to parse log entry:', e)
          }
        }

        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
        }

        ws.onclose = () => {
          console.log('WebSocket closed, reconnecting in 3s...')
          if (shouldReconnect) {
            reconnectTimeout = setTimeout(connect, 3000)
          }
        }
      } catch (error) {
        console.error('Failed to connect WebSocket:', error)
        if (shouldReconnect) {
          reconnectTimeout = setTimeout(connect, 3000)
        }
      }
    }

    connect()

    return () => {
      shouldReconnect = false
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
      if (ws) ws.close()
    }
  }, [isPaused])

  // Handle scroll behavior
  useEffect(() => {
    if (isAutoScroll && !userScrolled && logsContainerRef.current) {
      // Scroll to bottom only if user hasn't manually scrolled
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, isAutoScroll, userScrolled])

  // Detect user scroll
  const handleScroll = () => {
    if (!logsContainerRef.current) return
    
    const { scrollTop, scrollHeight, clientHeight } = logsContainerRef.current
    const isAtBottom = Math.abs(scrollHeight - scrollTop - clientHeight) < 50
    
    setUserScrolled(!isAtBottom)
  }

  const handleClear = () => {
    setLogs([])
  }

  const handleExport = () => {
    const logText = logs
      .map((log) => `[${dayjs(log.timestamp).format('HH:mm:ss.SSS')}] [${log.level}] ${log.message}`)
      .join('\n')
    
    const blob = new Blob([logText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `arbitrage-logs-${dayjs().format('YYYY-MM-DD-HHmmss')}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'INFO': return '#90CAF9'
      case 'WARN': return '#FFB74D'
      case 'ERROR': return '#EF5350'
      case 'SUCCESS': return '#66BB6A'
      case 'OPPORTUNITY': return '#FFD700'
      default: return '#BDBDBD'
    }
  }

  const filteredLogs = logs.filter((log) => {
    const matchesText = filter === '' || 
      log.message.toLowerCase().includes(filter.toLowerCase()) ||
      log.exchange?.toLowerCase().includes(filter.toLowerCase()) ||
      log.symbol?.toLowerCase().includes(filter.toLowerCase())
    
    const matchesLevel = levelFilter === 'ALL' || log.level === levelFilter
    
    return matchesText && matchesLevel
  })

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, mb: 3 }}>
        🔴 LIVE LOGS
      </Typography>

      {/* Controls */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
          <IconButton
            color={isPaused ? 'primary' : 'error'}
            onClick={() => setIsPaused(!isPaused)}
            size="large"
          >
            {isPaused ? <PlayArrow /> : <Pause />}
          </IconButton>

          <FormControlLabel
            control={
              <Switch
                checked={isAutoScroll}
                onChange={(e) => setIsAutoScroll(e.target.checked)}
              />
            }
            label="Auto-scroll"
          />

          <TextField
            size="small"
            placeholder="Filter logs..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            sx={{ minWidth: 200 }}
          />

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Level</InputLabel>
            <Select
              value={levelFilter}
              label="Level"
              onChange={(e) => setLevelFilter(e.target.value)}
            >
              <MenuItem value="ALL">All</MenuItem>
              <MenuItem value="INFO">Info</MenuItem>
              <MenuItem value="WARN">Warn</MenuItem>
              <MenuItem value="ERROR">Error</MenuItem>
              <MenuItem value="SUCCESS">Success</MenuItem>
              <MenuItem value="OPPORTUNITY">Opportunity</MenuItem>
            </Select>
          </FormControl>

          <Box sx={{ flexGrow: 1 }} />

          <Chip
            label={`${filteredLogs.length} logs`}
            color="primary"
            variant="outlined"
          />

          <IconButton onClick={handleClear} title="Clear logs">
            <Clear />
          </IconButton>

          <IconButton onClick={handleExport} title="Export logs">
            <Download />
          </IconButton>
        </Stack>
      </Paper>

      {/* Logs Container */}
      <Paper
        ref={logsContainerRef}
        onScroll={handleScroll}
        sx={{
          height: 'calc(100vh - 280px)',
          overflow: 'auto',
          bgcolor: '#1E1E1E',
          p: 2,
          fontFamily: '"Fira Code", "Courier New", monospace',
          fontSize: '0.875rem',
        }}
      >
        {filteredLogs.length === 0 ? (
          <Typography color="text.secondary" textAlign="center" sx={{ mt: 4 }}>
            {isPaused ? '⏸️ Paused' : '⏳ Waiting for logs...'}
          </Typography>
        ) : (
          filteredLogs.map((log) => (
            <Box
              key={log.id}
              sx={{
                mb: 0.5,
                p: 1,
                borderRadius: 1,
                '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.05)' },
                display: 'flex',
                alignItems: 'flex-start',
                gap: 1,
              }}
            >
              <Typography
                component="span"
                sx={{
                  color: '#666',
                  minWidth: 100,
                  fontFamily: 'inherit',
                }}
              >
                {dayjs(log.timestamp).format('HH:mm:ss.SSS')}
              </Typography>

              <Chip
                label={log.level}
                size="small"
                sx={{
                  bgcolor: getLevelColor(log.level),
                  color: '#000',
                  fontWeight: 700,
                  minWidth: 90,
                  fontFamily: 'inherit',
                }}
              />

              {log.exchange && (
                <Chip
                  label={log.exchange}
                  size="small"
                  variant="outlined"
                  sx={{
                    color: '#90CAF9',
                    borderColor: '#90CAF9',
                    fontFamily: 'inherit',
                  }}
                />
              )}

              {log.symbol && (
                <Chip
                  label={log.symbol}
                  size="small"
                  variant="outlined"
                  sx={{
                    color: '#FFD700',
                    borderColor: '#FFD700',
                    fontFamily: 'inherit',
                  }}
                />
              )}

              <Typography
                component="span"
                sx={{
                  color: '#FFF',
                  flex: 1,
                  fontFamily: 'inherit',
                  wordBreak: 'break-word',
                }}
              >
                {log.message}
              </Typography>
            </Box>
          ))
        )}
        <div ref={logsEndRef} />
      </Paper>

      {userScrolled && isAutoScroll && (
        <Box
          sx={{
            position: 'fixed',
            bottom: 20,
            right: 20,
            bgcolor: 'primary.main',
            color: 'white',
            px: 2,
            py: 1,
            borderRadius: 2,
            cursor: 'pointer',
            boxShadow: 3,
          }}
          onClick={() => {
            logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
            setUserScrolled(false)
          }}
        >
          ↓ New logs below
        </Box>
      )}
    </Box>
  )
}

