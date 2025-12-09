import { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Stack,
  Chip,
  LinearProgress,
  Card,
  CardContent,
} from '@mui/material'
import {
  TrendingUp,
  Speed,
  AccountBalance,
  SwapHoriz,
  Warning,
  CheckCircle,
} from '@mui/icons-material'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { arbitrageAPI } from '../services/api'
import dayjs from 'dayjs'

interface DashboardStats {
  engine_status: 'RUNNING' | 'STOPPED' | 'ERROR'
  uptime_seconds: number
  connected_exchanges: number
  total_exchanges: number
  balance_usd: number
  total_operations: number
  total_profit: number
  avg_spread_bps: number
  avg_execution_time_us: number
  opportunities_found: number
  opportunities_executed: number
  win_rate_percent: number
  best_pair: string | null
  worst_pair: string | null
}

interface ProfitPoint {
  timestamp: number
  profit: number
  cumulative: number
}

export default function ArbitrageDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [profitHistory, setProfitHistory] = useState<ProfitPoint[]>([])
  const [loading, setLoading] = useState(true)

  const fetchDashboard = async () => {
    try {
      const [statsRes, historyRes] = await Promise.all([
        arbitrageAPI.getStats(),
        arbitrageAPI.getProfitHistory(),
      ])
      setStats(statsRes.data)
      setProfitHistory(historyRes.data)
    } catch (error) {
      console.error('Failed to fetch dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
    const interval = setInterval(fetchDashboard, 5000) // Refresh every 5s
    return () => clearInterval(interval)
  }, [])

  if (loading || !stats) {
    return (
      <Box sx={{ width: '100%', mt: 4 }}>
        <LinearProgress />
      </Box>
    )
  }

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hours}h ${minutes}m ${secs}s`
  }

  const executionRate = stats.opportunities_found > 0
    ? ((stats.opportunities_executed / stats.opportunities_found) * 100).toFixed(1)
    : '0.0'

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, mb: 3 }}>
        ⚡ ARBITRAGE DASHBOARD
      </Typography>

      {/* Engine Status */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: stats.engine_status === 'RUNNING' ? 'success.dark' : 'error.dark' }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={2}>
            {stats.engine_status === 'RUNNING' ? (
              <CheckCircle sx={{ fontSize: 40, color: 'success.light' }} />
            ) : (
              <Warning sx={{ fontSize: 40, color: 'error.light' }} />
            )}
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 700, color: 'white' }}>
                Engine {stats.engine_status}
              </Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                Uptime: {formatUptime(stats.uptime_seconds)}
              </Typography>
            </Box>
          </Stack>

          <Stack direction="row" spacing={2}>
            <Chip
              label={`${stats.connected_exchanges}/${stats.total_exchanges} Exchanges`}
              color={stats.connected_exchanges === stats.total_exchanges ? 'success' : 'warning'}
              sx={{ fontWeight: 700 }}
            />
          </Stack>
        </Stack>
      </Paper>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Balance
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    ${stats.balance_usd.toFixed(2)}
                  </Typography>
                </Box>
                <AccountBalance sx={{ fontSize: 40, color: 'primary.main', opacity: 0.3 }} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Total Profit
                  </Typography>
                  <Typography
                    variant="h5"
                    sx={{
                      fontWeight: 700,
                      color: stats.total_profit >= 0 ? 'success.main' : 'error.main',
                    }}
                  >
                    ${stats.total_profit.toFixed(2)}
                  </Typography>
                </Box>
                <TrendingUp sx={{ fontSize: 40, color: 'success.main', opacity: 0.3 }} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Operations
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    {stats.total_operations}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'success.main' }}>
                    {stats.win_rate_percent.toFixed(1)}% Win Rate
                  </Typography>
                </Box>
                <SwapHoriz sx={{ fontSize: 40, color: 'info.main', opacity: 0.3 }} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Avg Speed
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    {stats.avg_execution_time_us < 1000
                      ? `${stats.avg_execution_time_us.toFixed(0)}μs`
                      : `${(stats.avg_execution_time_us / 1000).toFixed(1)}ms`}
                  </Typography>
                </Box>
                <Speed sx={{ fontSize: 40, color: 'warning.main', opacity: 0.3 }} />
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
              💰 Cumulative Profit
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={profitHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(ts) => dayjs(ts).format('HH:mm')}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(ts) => dayjs(ts).format('MMM D, HH:mm:ss')}
                  formatter={(value: number) => [`$${value.toFixed(2)}`, 'Profit']}
                />
                <Line
                  type="monotone"
                  dataKey="cumulative"
                  stroke="#66BB6A"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, mb: 2 }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
              📊 Performance
            </Typography>

            <Stack spacing={2}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Avg Spread
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  {stats.avg_spread_bps.toFixed(2)} bps
                </Typography>
              </Box>

              <Box>
                <Typography variant="caption" color="text.secondary">
                  Opportunities Found
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  {stats.opportunities_found}
                </Typography>
              </Box>

              <Box>
                <Typography variant="caption" color="text.secondary">
                  Execution Rate
                </Typography>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <LinearProgress
                    variant="determinate"
                    value={parseFloat(executionRate)}
                    sx={{ flex: 1, height: 8, borderRadius: 1 }}
                  />
                  <Typography variant="body2" sx={{ fontWeight: 700 }}>
                    {executionRate}%
                  </Typography>
                </Stack>
              </Box>
            </Stack>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 700 }}>
              🎯 Best Pairs
            </Typography>

            <Stack spacing={1}>
              {stats.best_pair && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Best
                  </Typography>
                  <Chip
                    label={stats.best_pair}
                    color="success"
                    size="small"
                    sx={{ fontWeight: 700 }}
                  />
                </Box>
              )}

              {stats.worst_pair && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Worst
                  </Typography>
                  <Chip
                    label={stats.worst_pair}
                    color="error"
                    size="small"
                    sx={{ fontWeight: 700 }}
                  />
                </Box>
              )}
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      {/* Info Card */}
      <Paper sx={{ p: 2, bgcolor: 'info.dark' }}>
        <Typography variant="body2" sx={{ color: 'white' }}>
          ℹ️ <strong>Arbitrage Bot V2.0.00 UNSTABLE</strong> - Ultra-low latency C engine with
          real-time multi-exchange arbitrage detection. Average execution: {stats.avg_execution_time_us.toFixed(0)}μs
        </Typography>
      </Paper>
    </Box>
  )
}

