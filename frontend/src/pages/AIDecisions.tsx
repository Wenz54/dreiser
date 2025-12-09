import { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
} from '@mui/material'
import { toast } from 'react-toastify'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat'
import InfoIcon from '@mui/icons-material/Info'
import BlockIcon from '@mui/icons-material/Block'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import api from '../services/api'
import { formatLocalDateTime } from '../utils/dateUtils'

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

export default function AIDecisions() {
  const [decisions, setDecisions] = useState<AIDecision[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedDecision, setSelectedDecision] = useState<AIDecision | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)

  useEffect(() => {
    fetchDecisions()
    const interval = setInterval(fetchDecisions, 15000) // Refresh every 15 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchDecisions = async () => {
    try {
      const response = await api.get('/ai/decisions?limit=50')
      // API returns {decisions: [...]}
      const decisionsData = response.data.decisions || response.data
      setDecisions(Array.isArray(decisionsData) ? decisionsData : [])
    } catch (error) {
      console.error('Failed to fetch AI decisions:', error)
      toast.error('Failed to load AI decisions.')
      setDecisions([])
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = (decision: AIDecision) => {
    setSelectedDecision(decision)
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setSelectedDecision(null)
  }

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

  const getDecisionColor = (decision: string) => {
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

  const getRejectionReason = (decision: AIDecision) => {
    if (decision.executed) return null
    
    // Проверяем market_data для определения причины отклонения
    const rr_ratio = decision.market_data?.risk_reward_ratio
    const confidence = decision.confidence
    
    if (confidence < 60) {
      return {
        label: `Low Confidence (${confidence}%)`,
        icon: <WarningAmberIcon fontSize="small" />,
        color: 'rgba(255, 255, 255, 0.3)'
      }
    }
    
    if (rr_ratio && rr_ratio < 1.3) {
      return {
        label: `Poor R:R (${rr_ratio.toFixed(2)}:1)`,
        icon: <BlockIcon fontSize="small" />,
        color: 'rgba(255, 255, 255, 0.3)'
      }
    }
    
    // HOLD решения
    if (decision.decision === 'HOLD') {
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

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ py: 2 }}>
      <Typography 
        variant="h3" 
        sx={{ 
          fontWeight: 300, 
          letterSpacing: '-0.02em',
          textTransform: 'uppercase',
          mb: 2
        }}
      >
        AI Trading Decisions
      </Typography>
      <Typography 
        variant="caption" 
        sx={{ 
          color: 'text.secondary',
          letterSpacing: '0.05em',
          display: 'block',
          mb: 4
        }}
      >
        DEEPSEEK AI analyzes 8 trading pairs every 2 minutes. Decisions with confidence ≥60% and R:R ≥1.3:1 are executed.
      </Typography>

      <Grid container spacing={2}>
        {decisions.map((decision) => {
          const rejection = getRejectionReason(decision)
          
          return (
          <Grid item xs={12} sm={6} md={4} key={decision.id}>
            <Card 
              sx={{ 
                cursor: 'pointer',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  border: '1px solid rgba(255, 255, 255, 0.2)'
                },
                border: decision.executed 
                  ? '1px solid rgba(255, 255, 255, 0.8)' 
                  : '1px solid rgba(255, 255, 255, 0.08)',
                opacity: decision.executed ? 1 : 0.7,
                position: 'relative'
              }}
              onClick={() => handleOpenDialog(decision)}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography 
                    variant="h6" 
                    sx={{ 
                      fontWeight: 300,
                      letterSpacing: '0.02em',
                      fontFamily: '"SF Mono", "Monaco", monospace'
                    }}
                  >
                    {decision.symbol}
                  </Typography>
                  {getDecisionIcon(decision.decision)}
                </Box>

                <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  <Chip 
                    label={decision.decision}
                    size="small"
                    sx={{ 
                      borderColor: 'rgba(255, 255, 255, 0.3)',
                      color: '#FFFFFF',
                      fontWeight: 500,
                      letterSpacing: '0.05em',
                      fontSize: '0.7rem'
                    }}
                    variant="outlined"
                  />
                  <Chip 
                    label={`${decision.confidence}%`}
                    variant="outlined"
                    size="small"
                    sx={{ 
                      borderColor: 'rgba(255, 255, 255, 0.2)',
                      fontFamily: 'monospace',
                      fontSize: '0.7rem'
                    }}
                  />
                  {decision.executed && (
                    <Chip 
                      label="EXECUTED"
                      size="small"
                      sx={{ 
                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        color: '#FFFFFF',
                        border: '1px solid rgba(255, 255, 255, 0.5)',
                        fontWeight: 600,
                        letterSpacing: '0.08em',
                        fontSize: '0.65rem'
                      }}
                    />
                  )}
                  {rejection && (
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
                          color: 'rgba(255, 255, 255, 0.5)'
                        }
                      }}
                    />
                  )}
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {decision.reasoning.substring(0, 100)}...
                </Typography>

                <Typography 
                  variant="caption" 
                  sx={{ 
                    color: 'text.secondary',
                    fontFamily: 'monospace',
                    fontSize: '0.7rem',
                    letterSpacing: '0.02em'
                  }}
                >
                  {formatLocalDateTime(decision.created_at)}
                </Typography>
              </CardContent>

              <CardActions sx={{ pt: 0, px: 2, pb: 2 }}>
                <Button 
                  size="small" 
                  startIcon={<InfoIcon />}
                  onClick={(e) => {
                    e.stopPropagation()
                    handleOpenDialog(decision)
                  }}
                  sx={{
                    color: 'rgba(255, 255, 255, 0.7)',
                    '&:hover': {
                      color: '#FFFFFF',
                      backgroundColor: 'rgba(255, 255, 255, 0.05)'
                    }
                  }}
                >
                  Details
                </Button>
              </CardActions>
            </Card>
          </Grid>
          )
        })}
      </Grid>

      {/* Details Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        {selectedDecision && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {getDecisionIcon(selectedDecision.decision)}
                <Typography variant="h6">
                  {selectedDecision.symbol} - {selectedDecision.decision}
                </Typography>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Box sx={{ mb: 2 }}>
                <Chip 
                  label={`${selectedDecision.confidence}% Confidence`}
                  color={getDecisionColor(selectedDecision.decision) as any}
                  sx={{ mr: 1 }}
                />
                {selectedDecision.executed && (
                  <Chip 
                    label="✓ Executed"
                    color="success"
                  />
                )}
              </Box>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                AI Reasoning:
              </Typography>
              <Typography variant="body1" paragraph>
                {selectedDecision.reasoning}
              </Typography>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                Market Data:
              </Typography>
              {selectedDecision.market_data && (
                <Box sx={{ bgcolor: 'background.paper', p: 2, borderRadius: 1 }}>
                  <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                    {JSON.stringify(selectedDecision.market_data, null, 2).substring(0, 500)}...
                  </Typography>
                </Box>
              )}

              <Divider sx={{ my: 2 }} />

              <Typography variant="caption" color="text.secondary">
                Decision made: {formatLocalDateTime(selectedDecision.created_at)}
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDialog}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  )
}

