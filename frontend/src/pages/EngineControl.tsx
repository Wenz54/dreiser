import { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Stack,
  Switch,
  FormControlLabel,
  TextField,
  Chip,
  Alert,
  Divider,
  Grid,
  Card,
  CardContent,
  Slider,
} from '@mui/material'
import {
  PlayArrow,
  Stop,
  RestartAlt,
  Settings,
  Speed,
  TrendingUp,
} from '@mui/icons-material'
import { engineAPI } from '../services/api'

interface EngineConfig {
  capital_usd?: number
  paper_mode?: boolean
  min_spread_bps?: number
  max_position_size_usd?: number
  max_open_positions?: number
  risk_percent?: number
  enabled_symbols?: string[]
  exchanges?: any
}

interface EngineStatus {
  running?: boolean
  uptime_seconds?: number
  connected_exchanges?: string[]
  active_positions?: number
  pending_orders?: number
}

export default function EngineControl() {
  const [status, setStatus] = useState<EngineStatus | null>(null)
  const [config, setConfig] = useState<EngineConfig | null>(null)
  const [localConfig, setLocalConfig] = useState<EngineConfig | null>(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [isEditing, setIsEditing] = useState(false)

  const fetchStatus = async () => {
    try {
      const [statusRes, configRes] = await Promise.all([
        engineAPI.getStatus(),
        engineAPI.getConfig(),
      ])
      setStatus(statusRes.data)
      
      // Only update config if not currently editing
      if (!isEditing) {
        setConfig(configRes.data)
        setLocalConfig(configRes.data)
      }
    } catch (error) {
      console.error('Failed to fetch engine status:', error)
    }
  }

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 3000)
    return () => clearInterval(interval)
  }, [isEditing])

  const handleStart = async () => {
    setLoading(true)
    setMessage(null)
    try {
      await engineAPI.start()
      setMessage({ type: 'success', text: '✅ Engine started successfully!' })
      
      // Wait a bit for engine to fully initialize
      await new Promise(resolve => setTimeout(resolve, 1500))
      await fetchStatus()
    } catch (error: any) {
      setMessage({ type: 'error', text: `❌ Failed to start: ${error.response?.data?.detail || error.message}` })
    } finally {
      setLoading(false)
    }
  }

  const handleStop = async () => {
    setLoading(true)
    setMessage(null)
    try {
      await engineAPI.stop()
      setMessage({ type: 'success', text: '🛑 Engine stopped successfully!' })
      
      // Wait a bit for engine to fully stop
      await new Promise(resolve => setTimeout(resolve, 1500))
      await fetchStatus()
    } catch (error: any) {
      setMessage({ type: 'error', text: `❌ Failed to stop: ${error.response?.data?.detail || error.message}` })
    } finally {
      setLoading(false)
    }
  }

  const handleRestart = async () => {
    setLoading(true)
    setMessage(null)
    try {
      await engineAPI.restart()
      setMessage({ type: 'success', text: '🔄 Engine restarted successfully!' })
      await fetchStatus()
    } catch (error: any) {
      setMessage({ type: 'error', text: `❌ Failed to restart: ${error.response?.data?.detail || error.message}` })
    } finally {
      setLoading(false)
    }
  }

  const handleSaveConfig = async () => {
    if (!localConfig) return
    
    setLoading(true)
    setMessage(null)
    try {
      await engineAPI.saveConfig(localConfig)
      setConfig(localConfig)
      setIsEditing(false)
      setMessage({ type: 'success', text: '💾 Configuration saved! Restart engine to apply.' })
      await fetchStatus()
    } catch (error: any) {
      setMessage({ type: 'error', text: `❌ Failed to save: ${error.response?.data?.detail || error.message}` })
    } finally {
      setLoading(false)
    }
  }
  
  const handleConfigChange = (updates: Partial<EngineConfig>) => {
    setIsEditing(true)
    setLocalConfig(prev => ({ ...prev, ...updates }))
  }

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hours}h ${minutes}m ${secs}s`
  }

  if (!status && !config && !localConfig) {
    return <Typography>Loading...</Typography>
  }
  
  // Default values if data is missing
  const safeStatus = status || {
    running: false,
    uptime_seconds: 0,
    connected_exchanges: [],
    active_positions: 0,
    pending_orders: 0
  }
  
  const defaultConfig = {
    min_spread_bps: 50,
    max_position_size_usd: 200,
    max_open_positions: 5,
    risk_percent: 2,
    enabled_symbols: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
    exchanges: {}
  }
  
  const safeConfig = localConfig || config || defaultConfig
  
  // Available trading pairs
  const availableSymbols = [
    'BTCUSDT',
    'ETHUSDT',
    'BNBUSDT',
    'SOLUSDT',
    'ADAUSDT',
    'DOGEUSDT',
    'XRPUSDT',
    'DOTUSDT',
    'MATICUSDT',
    'LINKUSDT'
  ]

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, mb: 3 }}>
        ⚙️ ENGINE CONTROL
      </Typography>

      {message && (
        <Alert severity={message.type} sx={{ mb: 3 }} onClose={() => setMessage(null)}>
          {message.text}
        </Alert>
      )}

      {/* Engine Status */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 3 }}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              Engine Status: {safeStatus.running ? '🟢 RUNNING' : '🔴 STOPPED'}
            </Typography>
            {safeStatus.running && (
              <Typography variant="body2" color="text.secondary">
                Uptime: {formatUptime(safeStatus.uptime_seconds || 0)}
              </Typography>
            )}
          </Box>

          <Stack direction="row" spacing={2}>
            <Button
              variant="contained"
              color="success"
              startIcon={<PlayArrow />}
              onClick={handleStart}
              disabled={safeStatus.running || loading}
              size="large"
            >
              START
            </Button>

            <Button
              variant="contained"
              color="error"
              startIcon={<Stop />}
              onClick={handleStop}
              disabled={!safeStatus.running || loading}
              size="large"
            >
              STOP
            </Button>

            <Button
              variant="outlined"
              startIcon={<RestartAlt />}
              onClick={handleRestart}
              disabled={!safeStatus.running || loading}
              size="large"
            >
              RESTART
            </Button>
          </Stack>
        </Stack>

        <Divider sx={{ my: 2 }} />

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="caption" color="text.secondary">
                  Connected Exchanges
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                  {safeStatus.connected_exchanges?.length || 0}
                </Typography>
                <Stack direction="row" spacing={0.5} flexWrap="wrap">
                  {(safeStatus.connected_exchanges || []).map((ex) => (
                    <Chip key={ex} label={ex} size="small" color="success" />
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="caption" color="text.secondary">
                  Active Positions
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  {safeStatus.active_positions || 0} / {safeConfig.max_open_positions || 5}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="caption" color="text.secondary">
                  Pending Orders
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  {safeStatus.pending_orders || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Configuration */}
      <Paper sx={{ p: 3 }}>
        <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
          <Settings />
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Configuration
          </Typography>
        </Stack>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>
              <Speed fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
              Minimum Spread (bps)
            </Typography>
            <TextField
              type="number"
              fullWidth
              value={safeConfig.min_spread_bps || 50}
              onChange={(e) =>
                handleConfigChange({ min_spread_bps: parseFloat(e.target.value) })
              }
              helperText="Minimum profitable spread to execute arbitrage"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>
              <TrendingUp fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
              Max Position Size (USD)
            </Typography>
            <TextField
              type="number"
              fullWidth
              value={safeConfig.max_position_size_usd || 200}
              onChange={(e) =>
                handleConfigChange({ max_position_size_usd: parseFloat(e.target.value) })
              }
              helperText="Maximum USD per single position"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>
              Max Open Positions
            </Typography>
            <Slider
              value={safeConfig.max_open_positions || 5}
              onChange={(_, value) =>
                handleConfigChange({ max_open_positions: value as number })
              }
              min={1}
              max={20}
              marks
              valueLabelDisplay="on"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>
              Risk Per Trade (%)
            </Typography>
            <Slider
              value={safeConfig.risk_percent || 2}
              onChange={(_, value) =>
                handleConfigChange({ risk_percent: value as number })
              }
              min={0.5}
              max={5}
              step={0.5}
              marks
              valueLabelDisplay="on"
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom>
              Enabled Exchanges
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Configure exchanges in engine.json file
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom>
              Enabled Symbols
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ gap: 1 }}>
              {availableSymbols.map((symbol) => (
                <FormControlLabel
                  key={symbol}
                  control={
                    <Switch
                      checked={(safeConfig.enabled_symbols || []).includes(symbol)}
                      onChange={(e) => {
                        const currentSymbols = safeConfig.enabled_symbols || []
                        const newSymbols = e.target.checked
                          ? [...currentSymbols, symbol]
                          : currentSymbols.filter((s) => s !== symbol)
                        handleConfigChange({ enabled_symbols: newSymbols })
                      }}
                      size="small"
                    />
                  }
                  label={symbol}
                  sx={{
                    border: '1px solid',
                    borderColor: (safeConfig.enabled_symbols || []).includes(symbol) ? 'primary.main' : 'divider',
                    borderRadius: 1,
                    px: 1,
                    m: 0,
                  }}
                />
              ))}
            </Stack>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Select trading pairs to enable
            </Typography>
          </Grid>
        </Grid>

        <Box sx={{ mt: 3, textAlign: 'right' }}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            onClick={handleSaveConfig}
            disabled={loading}
          >
            💾 SAVE CONFIGURATION
          </Button>
        </Box>
      </Paper>
    </Box>
  )
}

