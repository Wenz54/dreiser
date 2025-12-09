import { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Grid,
  Alert,
} from '@mui/material'
import { Download as DownloadIcon, TrendingUp as TrendingUpIcon, TrendingDown as TrendingDownIcon } from '@mui/icons-material'
import api from '../services/api'
import { formatLocalDateTime } from '../utils/dateUtils'

export default function Portfolio() {
  const [positions, setPositions] = useState<any[]>([])
  const [futuresPositions, setFuturesPositions] = useState<any[]>([])
  const [transactions, setTransactions] = useState<any[]>([])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000) // Обновлять каждые 10 сек
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [positionsRes, futuresRes, transactionsRes] = await Promise.all([
        api.get('/portfolio/positions'),
        api.get('/portfolio/futures-positions'),
        api.get('/trading/history'),
      ])

      setPositions(positionsRes.data.positions || [])
      setFuturesPositions(futuresRes.data.futures_positions || [])
      setTransactions(transactionsRes.data.transactions || [])
    } catch (error) {
      console.error('Failed to fetch portfolio data:', error)
    }
  }

  const handleExportReport = async () => {
    try {
      const response = await api.get('/portfolio/export-md', {
        responseType: 'blob',
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'draizer_report.md')
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Failed to export report:', error)
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Portfolio</Typography>
        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={handleExportReport}
        >
          Export Report (.md)
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* SPOT Positions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                SPOT Positions
              </Typography>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Regular buy/sell trades without leverage
              </Typography>
              {positions.length > 0 ? (
                <TableContainer component={Paper} sx={{ mt: 2 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Symbol</TableCell>
                        <TableCell align="right">Qty</TableCell>
                        <TableCell align="right">Entry</TableCell>
                        <TableCell align="right">Current</TableCell>
                        <TableCell align="right">P&L</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {positions.map((pos) => (
                        <TableRow key={pos.id}>
                          <TableCell>
                            <Chip label={pos.symbol} size="small" color="default" />
                          </TableCell>
                          <TableCell align="right">{Number(pos.quantity).toFixed(6)}</TableCell>
                          <TableCell align="right">${Number(pos.entry_price).toFixed(2)}</TableCell>
                          <TableCell align="right">${pos.current_price ? Number(pos.current_price).toFixed(2) : '-'}</TableCell>
                          <TableCell
                            align="right"
                            sx={{
                              color: pos.unrealized_pnl >= 0 ? 'success.main' : 'error.main',
                              fontWeight: 'bold'
                            }}
                          >
                            ${Number(pos.unrealized_pnl).toFixed(2)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  No open SPOT positions
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* FUTURES Positions */}
        <Grid item xs={12}>
          <Card sx={{ background: 'linear-gradient(135deg, #667eea15, #764ba215)' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                FUTURES Positions (3x Leverage)
              </Typography>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                LONG (bet on rise) / SHORT (bet on fall)
              </Typography>
              {futuresPositions.length > 0 ? (
                <TableContainer component={Paper} sx={{ mt: 2 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Symbol</TableCell>
                        <TableCell>Side</TableCell>
                        <TableCell align="right">Entry</TableCell>
                        <TableCell align="right">Current</TableCell>
                        <TableCell align="right">Margin</TableCell>
                        <TableCell align="right">P&L</TableCell>
                        <TableCell align="right">Liq.</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {futuresPositions.map((pos) => (
                        <TableRow key={pos.id}>
                          <TableCell>
                            <Chip label={pos.symbol} size="small" color="secondary" />
                          </TableCell>
                          <TableCell>
                            {pos.side === 'LONG' ? (
                              <Chip 
                                icon={<TrendingUpIcon />} 
                                label="LONG" 
                                size="small" 
                                color="success" 
                                sx={{ fontWeight: 'bold' }}
                              />
                            ) : (
                              <Chip 
                                icon={<TrendingDownIcon />} 
                                label="SHORT" 
                                size="small" 
                                color="error" 
                                sx={{ fontWeight: 'bold' }}
                              />
                            )}
                          </TableCell>
                          <TableCell align="right">${Number(pos.entry_price).toFixed(2)}</TableCell>
                          <TableCell align="right">${Number(pos.current_price).toFixed(2)}</TableCell>
                          <TableCell align="right">
                            <Typography variant="caption" color="text.secondary">
                              ${Number(pos.margin).toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell
                            align="right"
                            sx={{
                              color: pos.unrealized_pnl >= 0 ? 'success.main' : 'error.main',
                              fontWeight: 'bold'
                            }}
                          >
                            ${Number(pos.unrealized_pnl).toFixed(2)}
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="caption" color="error.main">
                              ${Number(pos.liquidation_price).toFixed(2)}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  No open FUTURES positions
                </Typography>
              )}
              
              {futuresPositions.length > 0 && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  <Typography variant="caption">
                    Liquidation происходит при движении цены на ±33% от entry price
                  </Typography>
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Trading History */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Trading History
          </Typography>
          {transactions.length > 0 ? (
            <TableContainer component={Paper} sx={{ mt: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Symbol</TableCell>
                    <TableCell align="right">Quantity</TableCell>
                    <TableCell align="right">Price</TableCell>
                    <TableCell align="right">Total</TableCell>
                    <TableCell align="right">P&L</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {transactions.slice(0, 20).map((tx) => (
                    <TableRow key={tx.id}>
                      <TableCell>{formatLocalDateTime(tx.executed_at)}</TableCell>
                      <TableCell>
                        <Chip
                          label={tx.type}
                          color={
                            tx.type === 'BUY' || tx.type === 'LONG' ? 'success' : 
                            tx.type === 'SELL' || tx.type === 'CLOSE_LONG' || tx.type === 'CLOSE_SHORT' ? 'error' :
                            tx.type === 'SHORT' ? 'secondary' :
                            'default'
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{tx.symbol}</TableCell>
                      <TableCell align="right">{Number(tx.quantity).toFixed(8)}</TableCell>
                      <TableCell align="right">${Number(tx.price).toFixed(2)}</TableCell>
                      <TableCell align="right">${Number(tx.total_value).toFixed(2)}</TableCell>
                      <TableCell
                        align="right"
                        sx={{
                          color: tx.pnl >= 0 ? 'success.main' : 'error.main',
                        }}
                      >
                        {tx.pnl ? `$${Number(tx.pnl).toFixed(2)}` : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No trading history
            </Typography>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}

