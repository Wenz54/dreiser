import { useEffect, useState } from 'react'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  RocketLaunch as RocketLaunchIcon,
} from '@mui/icons-material'
import { toast } from 'react-toastify'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

export default function Dashboard() {
  const navigate = useNavigate()
  const [portfolio, setPortfolio] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [portfolioRes, statsRes] = await Promise.all([
        api.get('/portfolio'),
        api.get('/portfolio/stats'),
      ])

      setPortfolio(portfolioRes.data)
      setStats(statsRes.data)
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = async () => {
    if (!window.confirm('⚠️ СБРОСИТЬ весь псевдо-счет и статистику? Все данные будут удалены!')) {
      return
    }

    try {
      await api.post('/portfolio/reset')
      toast.success('✅ Portfolio reset successfully!')
      // Перезагрузить данные
      await fetchData()
    } catch (error: any) {
      console.error('Failed to reset portfolio:', error)
      toast.error(error.response?.data?.detail || 'Failed to reset portfolio')
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  const isProfitable = stats?.total_pnl >= 0

  return (
    <Box sx={{ py: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 6 }}>
        <Typography 
          variant="h3" 
          sx={{ 
            fontWeight: 300, 
            letterSpacing: '-0.02em',
            textTransform: 'uppercase' 
          }}
        >
          Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            size="large"
            onClick={handleReset}
            sx={{ 
              color: '#FFFFFF',
              borderColor: 'rgba(255, 255, 255, 0.3)',
              '&:hover': {
                borderColor: '#FFFFFF',
                backgroundColor: 'rgba(255, 0, 0, 0.05)'
              }
            }}
          >
            RESET
          </Button>
          <Button
            variant="contained"
            size="large"
            startIcon={<RocketLaunchIcon />}
            onClick={() => navigate('/ai-session')}
          >
            Launch AI Session
          </Button>
        </Box>
      </Box>
      
      <Alert 
        severity="info" 
        sx={{ 
          mb: 4,
          backgroundColor: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          '& .MuiAlert-message': {
            color: '#A0A0A0'
          }
        }}
      >
        <Typography variant="caption" sx={{ letterSpacing: '0.05em' }}>
          <strong style={{ color: '#FFFFFF' }}>DEEPSEEK AI ANALYSIS:</strong> 8 trading pairs analyzed every 2 minutes. 
          Estimated cost: $29.60/month for continuous operation.
        </Typography>
      </Alert>
      <Typography 
        variant="overline" 
        sx={{ 
          color: 'text.secondary',
          display: 'block',
          mb: 4,
          opacity: 0.5
        }}
      >
        Virtual Trading Simulation — No Real Capital at Risk
      </Typography>

      <Grid container spacing={4} sx={{ mt: 1 }}>
        {/* Balance Card */}
        <Grid item xs={12} md={6} lg={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography 
                variant="overline" 
                sx={{ 
                  color: 'text.secondary',
                  display: 'block',
                  mb: 3
                }}
              >
                Virtual Balance
              </Typography>
              <Typography 
                variant="h3" 
                sx={{ 
                  fontFamily: '"SF Mono", "Monaco", "Inconsolata", "Roboto Mono", monospace',
                  fontWeight: 300,
                  letterSpacing: '-0.02em'
                }}
              >
                ${portfolio?.balance_usd ? Number(portfolio.balance_usd).toFixed(2) : '0.00'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Total P&L Card */}
        <Grid item xs={12} md={6} lg={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography 
                variant="overline" 
                sx={{ 
                  color: 'text.secondary',
                  display: 'block',
                  mb: 3
                }}
              >
                Total P&L
              </Typography>
              <Typography
                variant="h3"
                sx={{ 
                  fontFamily: '"SF Mono", "Monaco", "Inconsolata", "Roboto Mono", monospace',
                  fontWeight: 300,
                  letterSpacing: '-0.02em',
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 1.5,
                  color: isProfitable ? '#FFFFFF' : '#FFFFFF'
                }}
              >
                {isProfitable ? <TrendingUpIcon fontSize="large" /> : <TrendingDownIcon fontSize="large" />}
                {isProfitable ? '+' : ''}${stats?.total_pnl ? Number(stats.total_pnl).toFixed(2) : '0.00'}
              </Typography>
              <Typography 
                variant="caption" 
                sx={{ 
                  color: 'text.secondary',
                  mt: 1,
                  display: 'block',
                  fontFamily: 'monospace'
                }}
              >
                {isProfitable ? '+' : ''}{stats?.total_pnl_percent ? Number(stats.total_pnl_percent).toFixed(2) : '0.00'}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Total Trades Card */}
        <Grid item xs={12} md={6} lg={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography 
                variant="overline" 
                sx={{ 
                  color: 'text.secondary',
                  display: 'block',
                  mb: 3
                }}
              >
                Total Trades
              </Typography>
              <Typography 
                variant="h3"
                sx={{ 
                  fontFamily: '"SF Mono", "Monaco", "Inconsolata", "Roboto Mono", monospace',
                  fontWeight: 300,
                  letterSpacing: '-0.02em'
                }}
              >
                {stats?.total_trades || 0}
              </Typography>
              <Typography 
                variant="caption" 
                sx={{ 
                  color: 'text.secondary',
                  mt: 1,
                  display: 'block'
                }}
              >
                {stats?.winning_trades || 0} wins · {stats?.losing_trades || 0} losses
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Win Rate Card */}
        <Grid item xs={12} md={6} lg={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography 
                variant="overline" 
                sx={{ 
                  color: 'text.secondary',
                  display: 'block',
                  mb: 3
                }}
              >
                Win Rate
              </Typography>
              <Typography 
                variant="h3"
                sx={{ 
                  fontFamily: '"SF Mono", "Monaco", "Inconsolata", "Roboto Mono", monospace',
                  fontWeight: 300,
                  letterSpacing: '-0.02em'
                }}
              >
                {stats?.win_rate ? Number(stats.win_rate).toFixed(1) : '0.0'}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography 
                variant="overline" 
                sx={{ 
                  display: 'block',
                  mb: 3,
                  color: 'text.secondary'
                }}
              >
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  onClick={() => window.location.href = '/ai'}
                  sx={{ minWidth: 200 }}
                >
                  Run AI Analysis
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => window.location.href = '/chat'}
                  sx={{ minWidth: 200 }}
                >
                  Ask AI Assistant
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => window.location.href = '/portfolio'}
                  sx={{ minWidth: 200 }}
                >
                  View Portfolio
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

