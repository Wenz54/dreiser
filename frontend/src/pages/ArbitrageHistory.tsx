import { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Stack,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Pagination,
  Tooltip,
} from '@mui/material'
import { Refresh, Download } from '@mui/icons-material'
import dayjs from 'dayjs'
import { operationsAPI } from '../services/api'

interface ArbitrageOperation {
  id: number
  timestamp: string
  type: string
  strategy: string
  symbol: string
  exchange_buy: string
  exchange_sell: string
  quantity: number
  entry_price: number
  exit_price: number
  pnl: number
  pnl_percent: number
  spread_bps: number
  fees_paid: number
  is_open: boolean
}

export default function ArbitrageHistory() {
  const [operations, setOperations] = useState<ArbitrageOperation[]>([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [filter, setFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('ALL')
  const [exchangeFilter, setExchangeFilter] = useState<string>('ALL')

  const fetchOperations = async () => {
    setLoading(true)
    try {
      const response = await operationsAPI.getLatest(50)
      let ops = response.data.operations || []
      
      // Apply filters
      if (statusFilter !== 'ALL') {
        ops = ops.filter((op: ArbitrageOperation) => 
          (statusFilter === 'OPEN' && op.is_open) || 
          (statusFilter === 'CLOSED' && !op.is_open)
        )
      }
      
      if (exchangeFilter !== 'ALL') {
        ops = ops.filter((op: ArbitrageOperation) => 
          op.exchange_buy === exchangeFilter || op.exchange_sell === exchangeFilter
        )
      }
      
      if (filter) {
        ops = ops.filter((op: ArbitrageOperation) => 
          op.symbol.toLowerCase().includes(filter.toLowerCase()) ||
          op.exchange_buy.toLowerCase().includes(filter.toLowerCase()) ||
          op.exchange_sell.toLowerCase().includes(filter.toLowerCase())
        )
      }
      
      setOperations(ops)
      setTotalPages(1) // All data in memory, no pagination
    } catch (error) {
      console.error('Failed to fetch operations:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchOperations()
  }, [page, statusFilter, exchangeFilter])

  const handleExport = async () => {
    try {
      // Export as CSV
      const csv = [
        'ID,Timestamp,Type,Strategy,Symbol,Exchange Buy,Exchange Sell,Quantity,Entry Price,Exit Price,PnL,PnL %,Spread BPS,Fees,Status',
        ...operations.map(op => 
          `${op.id},${dayjs(op.timestamp).format('YYYY-MM-DD HH:mm:ss')},${op.type},${op.strategy},${op.symbol},${op.exchange_buy},${op.exchange_sell},${op.quantity},${op.entry_price},${op.exit_price},${op.pnl},${op.pnl_percent},${op.spread_bps},${op.fees_paid},${op.is_open ? 'OPEN' : 'CLOSED'}`
        )
      ].join('\n')
      
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `arbitrage-history-${dayjs().format('YYYY-MM-DD')}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export:', error)
    }
  }

  const getStatusColor = (is_open: boolean, pnl: number) => {
    if (is_open) return 'info'
    return pnl >= 0 ? 'success' : 'error'
  }

  const totalProfit = operations.reduce((sum, op) => sum + op.pnl, 0)
  const successRate = operations.length > 0
    ? (operations.filter((op) => !op.is_open && op.pnl > 0).length / operations.filter(op => !op.is_open).length) * 100
    : 0

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, mb: 3 }}>
        📊 ARBITRAGE HISTORY
      </Typography>

      {/* Stats */}
      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <Paper sx={{ p: 2, flex: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Total Operations
          </Typography>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            {operations.length}
          </Typography>
        </Paper>

        <Paper sx={{ p: 2, flex: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Total Net Profit
          </Typography>
          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              color: totalProfit >= 0 ? 'success.main' : 'error.main',
            }}
          >
            ${totalProfit.toFixed(2)}
          </Typography>
        </Paper>

        <Paper sx={{ p: 2, flex: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Success Rate
          </Typography>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            {successRate.toFixed(1)}%
          </Typography>
        </Paper>
      </Stack>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
          <TextField
            size="small"
            placeholder="Search symbol..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            sx={{ minWidth: 200 }}
          />

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="ALL">All</MenuItem>
              <MenuItem value="OPEN">Open</MenuItem>
              <MenuItem value="CLOSED">Closed</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Exchange</InputLabel>
            <Select
              value={exchangeFilter}
              label="Exchange"
              onChange={(e) => setExchangeFilter(e.target.value)}
            >
              <MenuItem value="ALL">All</MenuItem>
              <MenuItem value="binance">Binance</MenuItem>
              <MenuItem value="mexc">MEXC</MenuItem>
              <MenuItem value="bybit">Bybit</MenuItem>
              <MenuItem value="okx">OKX</MenuItem>
              <MenuItem value="gateio">Gate.io</MenuItem>
              <MenuItem value="kucoin">KuCoin</MenuItem>
              <MenuItem value="huobi">Huobi</MenuItem>
              <MenuItem value="bitget">Bitget</MenuItem>
            </Select>
          </FormControl>

          <Box sx={{ flexGrow: 1 }} />

          <IconButton onClick={fetchOperations} disabled={loading} title="Refresh">
            <Refresh />
          </IconButton>

          <IconButton onClick={handleExport} title="Export CSV">
            <Download />
          </IconButton>
        </Stack>
      </Paper>

      {/* Table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'primary.dark' }}>
              <TableCell sx={{ color: 'white', fontWeight: 700 }}>Time</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 700 }}>Type</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 700 }}>Strategy</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 700 }}>Symbol</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 700 }}>Buy @</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 700 }}>Sell @</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 700 }} align="right">
                Quantity
              </TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 700 }} align="right">
                Entry
              </TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 700 }} align="right">
                Exit
              </TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 700 }} align="right">
                PnL
              </TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 700 }} align="right">
                PnL %
              </TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 700 }} align="right">
                Spread
              </TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 700 }}>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {operations.map((op) => (
              <TableRow
                key={op.id}
                sx={{ '&:hover': { bgcolor: 'action.hover' } }}
              >
                <TableCell>
                  {dayjs(op.timestamp).format('MMM D, HH:mm:ss')}
                </TableCell>
                <TableCell>
                  <Chip 
                    label={op.type} 
                    size="small" 
                    color={op.type === 'LONG' ? 'success' : op.type === 'SHORT' ? 'error' : 'default'}
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="caption">{op.strategy}</Typography>
                </TableCell>
                <TableCell>
                  <Typography sx={{ fontWeight: 700 }}>{op.symbol}</Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={op.exchange_buy}
                    size="small"
                    color="success"
                    sx={{ fontSize: '0.7rem' }}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={op.exchange_sell}
                    size="small"
                    color="error"
                    sx={{ fontSize: '0.7rem' }}
                  />
                </TableCell>
                <TableCell align="right">{op.quantity.toFixed(4)}</TableCell>
                <TableCell align="right">
                  <Typography variant="body2">
                    ${op.entry_price.toFixed(6)}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="body2">
                    ${op.exit_price > 0 ? op.exit_price.toFixed(6) : '-'}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography
                    sx={{
                      fontWeight: 700,
                      color: op.pnl >= 0 ? 'success.main' : 'error.main',
                    }}
                  >
                    ${op.pnl.toFixed(2)}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography
                    sx={{
                      fontWeight: 700,
                      color: op.pnl_percent >= 0 ? 'success.main' : 'error.main',
                    }}
                  >
                    {op.pnl_percent.toFixed(2)}%
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography
                    sx={{
                      fontWeight: 700,
                      color: op.spread_bps >= 50 ? 'success.main' : 'text.primary',
                    }}
                  >
                    {op.spread_bps.toFixed(2)} bps
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={op.is_open ? 'OPEN' : 'CLOSED'}
                    size="small"
                    color={getStatusColor(op.is_open, op.pnl) as any}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
        <Pagination
          count={totalPages}
          page={page}
          onChange={(_, value) => setPage(value)}
          color="primary"
        />
      </Box>
    </Box>
  )
}

