import { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Grid,
  Alert,
  LinearProgress,
  Chip,
  Divider,
  CardActions,
} from '@mui/material'
import { toast } from 'react-toastify'
import api from '../services/api'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import StopIcon from '@mui/icons-material/Stop'
import RefreshIcon from '@mui/icons-material/Refresh'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import BlockIcon from '@mui/icons-material/Block'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'

interface AISessionStatus {
  is_active: boolean
  session_id?: string
  started_at?: string
  ends_at?: string
  remaining_minutes?: number
  total_analyses?: number
  total_trades?: number
  next_analysis_in?: string
  message?: string
  performance_score?: {
    score: number
    total_trades: number
    winning_trades: number
    total_pnl: number
    last_change_reason: string
  }
}

interface AIDecision {
  id: string
  symbol: string
  decision: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
  reasoning: string
  executed: boolean
  created_at: string
  market_data?: any
}

interface PairAnalysis {
  symbol: string
  action: 'BUY' | 'SELL' | 'WAIT' | 'LONG' | 'SHORT' | 'CLOSE_LONG' | 'CLOSE_SHORT'
  confidence: number
  expectation: string
  reasoning: string
  target_price: number
  stop_loss: number
  time_horizon: string
  current_price: number
  executed: boolean
  created_at: string
}

interface AutonomousAnalysis {
  timestamp: string | null
  pairs: Record<string, PairAnalysis>
  total_pairs: number
  executed_count: number
}

export default function AISession() {
  const [sessionStatus, setSessionStatus] = useState<AISessionStatus | null>(null)
  const [autonomousAnalysis, setAutonomousAnalysis] = useState<AutonomousAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const sessionDurationHours = 10

  useEffect(() => {
    fetchSessionStatus()
    fetchAutonomousAnalysis()
    const interval = setInterval(() => {
      fetchSessionStatus()
      fetchAutonomousAnalysis()
    }, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchSessionStatus = async () => {
    try {
      const response = await api.get<AISessionStatus>('/ai-session/status')
      setSessionStatus(response.data)
    } catch (error) {
      console.error('Failed to fetch AI session status:', error)
      setSessionStatus({ is_active: false, message: 'Failed to load status.' })
    } finally {
      setLoading(false)
    }
  }

  const fetchAutonomousAnalysis = async () => {
    try {
      const response = await api.get<AutonomousAnalysis>('/ai-analysis/latest')
      setAutonomousAnalysis(response.data)
    } catch (error) {
      console.error('Failed to fetch autonomous analysis:', error)
      setAutonomousAnalysis(null)
    }
  }

  const startSession = async () => {
    setActionLoading(true)
    try {
      await api.post(`/ai-session/start?duration_hours=${sessionDurationHours}`)
      toast.success('AI Session started successfully!')
      await fetchSessionStatus()
    } catch (error: any) {
      console.error('Failed to start AI session:', error)
      const errorMsg = error.response?.data?.detail || 'Failed to start AI session.'
      toast.error(errorMsg)
    } finally {
      setActionLoading(false)
    }
  }

  const stopSession = async () => {
    setActionLoading(true)
    try {
      await api.post('/ai-session/stop')
      toast.info('AI Session stopped.')
      await fetchSessionStatus()
    } catch (error: any) {
      console.error('Failed to stop AI session:', error)
      const errorMsg = error.response?.data?.detail || 'Failed to stop AI session.'
      toast.error(errorMsg)
    } finally {
      setActionLoading(false)
    }
  }

  const progress = sessionStatus?.is_active && sessionStatus.remaining_minutes !== undefined
    ? ((sessionDurationHours * 60 - sessionStatus.remaining_minutes) / (sessionDurationHours * 60)) * 100
    : 0

  const estimatedCost = 0.02 // ~$0.02 for 1 hour

  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'BUY':
        return <TrendingUpIcon color="success" />
      case 'SELL':
        return <TrendingDownIcon color="error" />
      case 'HOLD':
        return <TrendingFlatIcon color="warning" />
      default:
        return null
    }
  }

  const getDecisionColor = (decision: string): 'success' | 'error' | 'warning' | 'default' => {
    switch (decision) {
      case 'BUY':
        return 'success'
      case 'SELL':
        return 'error'
      case 'HOLD':
        return 'warning'
      default:
        return 'default'
    }
  }

  const getScoreColor = (score: number): string => {
    // Монохромная шкала: белый (100) -> тёмно-серый (0)
    const intensity = Math.round(255 - (255 - 66) * (1 - score / 100))
    return `rgb(${intensity}, ${intensity}, ${intensity})`
  }

  const getRejectionReason = (pair: PairAnalysis) => {
    if (pair.executed) return null
    
    // Проверяем причину отклонения на основе данных
    const confidence = pair.confidence
    
    // Для FUTURES операций проверяем R:R (должен быть >= 1.3 для цели 0.6%/час)
    if (['SHORT', 'LONG'].includes(pair.action)) {
      const current = pair.current_price
      const target = pair.target_price
      const stop = pair.stop_loss
      
      if (current && target && stop) {
        let rr_ratio = 0
        if (pair.action === 'SHORT') {
          const reward = current - target
          const risk = stop - current
          rr_ratio = risk > 0 ? reward / risk : 0
        } else {
          const reward = target - current
          const risk = current - stop
          rr_ratio = risk > 0 ? reward / risk : 0
        }
        
        if (rr_ratio < 1.3) {
          return {
            label: `Poor R:R (${rr_ratio.toFixed(2)}:1 < 1.3:1)`,
            icon: <BlockIcon fontSize="small" />,
            color: 'rgba(255, 255, 255, 0.3)'
          }
        }
      }
    }
    
    if (confidence < 60) {
      return {
        label: `Low Confidence (${confidence}% < 60%)`,
        icon: <WarningAmberIcon fontSize="small" />,
        color: 'rgba(255, 255, 255, 0.3)'
      }
    }
    
    // WAIT решения
    if (pair.action === 'WAIT') {
      return {
        label: 'Market Observation',
        icon: <TrendingFlatIcon fontSize="small" />,
        color: 'rgba(255, 255, 255, 0.2)'
      }
    }
    
    return {
      label: 'Not Executed',
      icon: <BlockIcon fontSize="small" />,
      color: 'rgba(255, 255, 255, 0.2)'
    }
  }

  const getScoreLabel = (score: number): string => {
    if (score >= 80) return 'Excellent'
    if (score >= 60) return 'Good'
    if (score >= 40) return 'Average'
    if (score >= 20) return 'Poor'
    return 'Critical'
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        AI TRADING SESSION
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Launch an autonomous AI trading session. The AI will analyze 8 crypto pairs and make virtual trades.
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {/* Session Control Card */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Session Control
              </Typography>
              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : (
                <>
                  {sessionStatus?.is_active ? (
                    <Alert severity="success" sx={{ mb: 2 }}>
                      <strong>AI Session is ACTIVE!</strong>
                      <br />
                      Time remaining: <strong>{sessionStatus.remaining_minutes} minutes</strong>
                    </Alert>
                  ) : (
                    <Alert severity="warning" sx={{ mb: 2 }}>
                      No active AI session.
                    </Alert>
                  )}

                  <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                    <Button
                      variant="contained"
                      color="success"
                      size="large"
                      startIcon={<PlayArrowIcon />}
                      onClick={startSession}
                      disabled={sessionStatus?.is_active || actionLoading}
                    >
                      {actionLoading ? <CircularProgress size={24} /> : `Start ${sessionDurationHours}-Hour Session`}
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      size="large"
                      startIcon={<StopIcon />}
                      onClick={stopSession}
                      disabled={!sessionStatus?.is_active || actionLoading}
                    >
                      Stop Session
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<RefreshIcon />}
                      onClick={fetchSessionStatus}
                      disabled={actionLoading}
                    >
                      Refresh
                    </Button>
                  </Box>

                  {sessionStatus?.is_active && (
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Progress: {progress.toFixed(1)}%
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={progress} 
                        sx={{ height: 10, borderRadius: 5, mb: 2 }}
                      />
                      
                      <Grid container spacing={2}>
                        <Grid item xs={6} sm={3}>
                          <Typography variant="caption" color="text.secondary">
                            Analyses
                          </Typography>
                          <Typography variant="h6">
                            {sessionStatus.total_analyses || 0}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Typography variant="caption" color="text.secondary">
                            Trades
                          </Typography>
                          <Typography variant="h6" color="primary">
                            {sessionStatus.total_trades || 0}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Typography variant="caption" color="text.secondary">
                            Next Analysis
                          </Typography>
                          <Typography variant="body2">
                            {sessionStatus.next_analysis_in || 'N/A'}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Typography variant="caption" color="text.secondary">
                            Session ID
                          </Typography>
                          <Typography variant="caption" sx={{ wordBreak: 'break-all' }}>
                            {sessionStatus.session_id?.substring(0, 8)}...
                          </Typography>
                        </Grid>
                      </Grid>
                    </Box>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Score Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                AI Performance Score
              </Typography>
              
              {sessionStatus?.performance_score ? (
                <>
                  <Box sx={{ position: 'relative', display: 'inline-flex', width: '100%', justifyContent: 'center', my: 3 }}>
                    <CircularProgress
                      variant="determinate"
                      value={sessionStatus.performance_score.score}
                      size={160}
                      thickness={8}
                      sx={{
                        transform: 'rotate(-90deg) !important',
                        '& .MuiCircularProgress-circle': {
                          strokeLinecap: 'round',
                          stroke: getScoreColor(sessionStatus.performance_score.score)
                        }
                      }}
                    />
                    <Box
                      sx={{
                        top: 0,
                        left: 0,
                        bottom: 0,
                        right: 0,
                        position: 'absolute',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Typography variant="h3" component="div" fontWeight="bold">
                        {sessionStatus.performance_score.score}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {getScoreLabel(sessionStatus.performance_score.score)}
                      </Typography>
                    </Box>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Trades:
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {sessionStatus.performance_score.total_trades}
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Winning Trades:
                    </Typography>
                    <Typography variant="body2" fontWeight="bold" color="success.main">
                      {sessionStatus.performance_score.winning_trades}
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total P&L:
                    </Typography>
                    <Typography 
                      variant="body2" 
                      fontWeight="bold"
                      color={sessionStatus.performance_score.total_pnl >= 0 ? 'success.main' : 'error.main'}
                    >
                      ${sessionStatus.performance_score.total_pnl.toFixed(2)}
                    </Typography>
                  </Box>

                  {sessionStatus.performance_score.last_change_reason && (
                    <Alert severity="info" sx={{ mt: 2, py: 0.5 }}>
                      <Typography variant="caption">
                        {sessionStatus.performance_score.last_change_reason}
                      </Typography>
                    </Alert>
                  )}
                </>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No performance data available
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Info Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Session Info
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Duration
                </Typography>
                <Chip label={`${sessionDurationHours} hours`} color="primary" />
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Trading Pairs
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  <Chip label="BTC" size="small" />
                  <Chip label="ETH" size="small" />
                  <Chip label="BNB" size="small" />
                  <Chip label="SOL" size="small" />
                  <Chip label="ADA" size="small" />
                  <Chip label="DOGE" size="small" />
                  <Chip label="XRP" size="small" />
                  <Chip label="DOT" size="small" />
                </Box>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  AI Analysis
                </Typography>
                <Typography variant="body1">
                  Every 2 minutes
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Trading Strategy
                </Typography>
                <Typography variant="body1">
                  Scalping (SPOT + Futures 3x)
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Performance Score
                </Typography>
                <Typography variant="body1">
                  0-100 (50 = neutral start)
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Estimated Cost
                </Typography>
                <Typography variant="h6" color="success.main">
                  ~${estimatedCost.toFixed(2)}
                </Typography>
              </Box>

              <Alert severity="info" sx={{ mt: 2 }}>
                <strong>Autonomous Mode:</strong> AI executes trades only when confidence ≥ 80%
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* AI Autonomous Analysis Section */}
      <Box sx={{ mt: 4 }}>
        <Divider sx={{ mb: 3 }} />
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          AI AUTONOMOUS ANALYSIS
          {autonomousAnalysis && (
            <Chip 
              label={`${autonomousAnalysis.total_pairs} PAIRS | ${autonomousAnalysis.executed_count} EXECUTED`} 
              size="small" 
              color="primary" 
              variant="outlined"
              sx={{ fontWeight: 700 }}
            />
          )}
        </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
            AI analyzes ALL 8 pairs every 50 seconds. Executes when confidence ≥ 55% (profit-focused, flexible timing 50sec-60min)
          </Typography>

        {!autonomousAnalysis || !autonomousAnalysis.timestamp ? (
          <Alert severity="info">
            No AI analysis yet. Start a session and wait ~50 seconds for first autonomous analysis.
          </Alert>
        ) : (
          <>
            {/* Timestamp */}
            <Alert severity="success" sx={{ mb: 3 }}>
              <Typography variant="body2">
                <strong>Last Analysis:</strong> {new Date(autonomousAnalysis.timestamp).toLocaleString()}
              </Typography>
            </Alert>

            {/* All Pairs Analysis - ONE CARD */}
            <Card sx={{ bgcolor: '#000000', border: '2px solid #FFFFFF' }}>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                  ALL 8 PAIRS - LATEST AI ANALYSIS
                </Typography>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {Object.values(autonomousAnalysis.pairs).map((pair, index) => {
                    const actionColor = 
                      pair.action === 'BUY' ? 'success' :
                      pair.action === 'SELL' ? 'error' :
                      pair.action === 'LONG' ? 'info' :
                      pair.action === 'SHORT' ? 'secondary' :
                      pair.action === 'CLOSE_LONG' ? 'info' :
                      pair.action === 'CLOSE_SHORT' ? 'secondary' :
                      'warning'
                    
                    const actionIcon = 
                      pair.action === 'BUY' ? <TrendingUpIcon /> :
                      pair.action === 'SELL' ? <TrendingDownIcon /> :
                      pair.action === 'LONG' ? <TrendingUpIcon /> :
                      pair.action === 'SHORT' ? <TrendingDownIcon /> :
                      pair.action === 'CLOSE_LONG' ? <CheckCircleIcon /> :
                      pair.action === 'CLOSE_SHORT' ? <CheckCircleIcon /> :
                      <TrendingFlatIcon />
                    
                    return (
                      <Box 
                        key={pair.symbol}
                        sx={{
                          p: 2,
                          bgcolor: pair.executed ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                          borderRadius: 0,
                          border: '2px solid #FFFFFF',
                          transition: 'all 0.2s',
                          '&:hover': {
                            bgcolor: 'rgba(255, 255, 255, 0.08)',
                            borderColor: '#FFFFFF'
                          }
                        }}
                      >
                        {/* Header Row */}
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          {/* Symbol & Price */}
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Typography variant="h6" sx={{ fontWeight: 'bold', minWidth: 100 }}>
                              {pair.symbol}
                            </Typography>
                            <Typography 
                              variant="h6" 
                              color="primary"
                              sx={{ fontFamily: '"SF Mono", "Monaco", monospace' }}
                            >
                              ${pair.current_price ? pair.current_price.toFixed(6) : 'N/A'}
                            </Typography>
                          </Box>

                          {/* Action Chips */}
                          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                            {actionIcon}
                            <Chip 
                              label={pair.action}
                              color={actionColor}
                              size="medium"
                              sx={{ fontWeight: 'bold', fontSize: '0.9rem' }}
                            />
                            <Chip 
                              label={`${pair.confidence}%`}
                              variant="outlined"
                              size="medium"
                              color={pair.confidence >= 80 ? 'success' : 'default'}
                              sx={{ fontWeight: 'bold' }}
                            />
                            {pair.executed && (
                              <Chip 
                                label="EXECUTED"
                                color="success"
                                size="medium"
                                sx={{ fontWeight: 700 }}
                              />
                            )}
                            {(() => {
                              const rejection = getRejectionReason(pair)
                              return rejection ? (
                                <Chip 
                                  icon={rejection.icon}
                                  label={rejection.label}
                                  size="small"
                                  sx={{ 
                                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                                    color: 'rgba(255, 255, 255, 0.5)',
                                    border: `1px solid ${rejection.color}`,
                                    fontWeight: 400,
                                    letterSpacing: '0.03em',
                                    fontSize: '0.65rem',
                                    '& .MuiChip-icon': {
                                      color: 'rgba(255, 255, 255, 0.4)'
                                    }
                                  }}
                                />
                              ) : null
                            })()}
                          </Box>
                        </Box>

                        <Divider sx={{ mb: 2 }} />

                        {/* Expectation */}
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                            EXPECTATION:
                          </Typography>
                          <Typography 
                            variant="body1" 
                            sx={{ 
                              fontWeight: 500,
                              color: 'text.primary',
                              fontStyle: 'italic'
                            }}
                          >
                            "{pair.expectation}"
                          </Typography>
                        </Box>

                        {/* Reasoning */}
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
                            REASONING:
                          </Typography>
                          <Typography 
                            variant="body2" 
                            color="text.secondary"
                          >
                            {pair.reasoning}
                          </Typography>
                        </Box>

                        {/* Targets & Horizon */}
                        {(pair.target_price > 0 || pair.stop_loss > 0 || pair.time_horizon) && (
                          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mt: 2, pt: 2, borderTop: '1px solid #FFFFFF' }}>
                            {pair.target_price > 0 && (
                              <Box>
                                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                                  TARGET
                                </Typography>
                                <Typography 
                                  variant="body1" 
                                  color="success.main" 
                                  sx={{ 
                                    fontWeight: 700,
                                    fontFamily: '"SF Mono", "Monaco", monospace'
                                  }}
                                >
                                  ${pair.target_price ? pair.target_price.toFixed(6) : 'N/A'}
                                </Typography>
                              </Box>
                            )}
                            {pair.stop_loss > 0 && (
                              <Box>
                                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                                  STOP LOSS
                                </Typography>
                                <Typography 
                                  variant="body1" 
                                  color="error.main" 
                                  sx={{ 
                                    fontWeight: 700,
                                    fontFamily: '"SF Mono", "Monaco", monospace'
                                  }}
                                >
                                  ${pair.stop_loss ? pair.stop_loss.toFixed(6) : 'N/A'}
                                </Typography>
                              </Box>
                            )}
                            {pair.time_horizon && (
                              <Box>
                                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                                  TIME
                                </Typography>
                                <Typography variant="body1" sx={{ fontWeight: 700 }}>
                                  {pair.time_horizon}
                                </Typography>
                              </Box>
                            )}
                          </Box>
                        )}

                        {/* Divider between pairs */}
                        {index < Object.values(autonomousAnalysis.pairs).length - 1 && (
                          <Divider sx={{ mt: 2 }} />
                        )}
                      </Box>
                    )
                  })}
                </Box>
              </CardContent>
            </Card>
          </>
        )}
      </Box>
    </Box>
  )
}
