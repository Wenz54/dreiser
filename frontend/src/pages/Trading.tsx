import { useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
} from '@mui/material'
import { toast } from 'react-toastify'
import api from '../services/api'

export default function Trading() {
  const [action, setAction] = useState<'BUY' | 'SELL'>('BUY')
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [amount, setAmount] = useState('')
  const [loading, setLoading] = useState(false)

  const handleTrade = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Please enter a valid amount')
      return
    }

    setLoading(true)
    try {
      const response = await api.post('/trading/manual-trade', {
        action,
        symbol,
        amount_usd: parseFloat(amount),
      })

      toast.success(`Virtual ${action} executed successfully!`)
      setAmount('')
      
      // Reload page to update data
      setTimeout(() => window.location.reload(), 1000)
    } catch (error) {
      console.error('Trade failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Manual Trading
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        ⚠️ This is virtual trading (simulation) - No real money
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Place Virtual Trade
              </Typography>

              <FormControl fullWidth sx={{ mt: 2 }}>
                <InputLabel>Action</InputLabel>
                <Select
                  value={action}
                  label="Action"
                  onChange={(e) => setAction(e.target.value as 'BUY' | 'SELL')}
                >
                  <MenuItem value="BUY">Buy</MenuItem>
                  <MenuItem value="SELL">Sell</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                sx={{ mt: 2 }}
                disabled
              />

              <TextField
                fullWidth
                label="Amount (USD)"
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                sx={{ mt: 2 }}
                helperText="Amount in USD to buy/sell"
              />

              <Button
                fullWidth
                variant="contained"
                color={action === 'BUY' ? 'success' : 'error'}
                onClick={handleTrade}
                disabled={loading}
                sx={{ mt: 3 }}
              >
                {loading ? 'Processing...' : `${action} ${symbol}`}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Manual Trading Info
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Manual trading allows you to execute virtual trades for testing purposes.
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                <strong>How it works:</strong>
              </Typography>
              <ul>
                <li>
                  <Typography variant="body2" color="text.secondary">
                    Fetches real BTC/USDT price from Binance
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" color="text.secondary">
                    Simulates trade execution with virtual balance
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" color="text.secondary">
                    No real money is used - this is paper trading
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" color="text.secondary">
                    All trades are recorded for analysis
                  </Typography>
                </li>
              </ul>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}







