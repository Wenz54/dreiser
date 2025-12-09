import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Chip,
  Grid,
  Paper,
} from '@mui/material'
import { Psychology as AIIcon } from '@mui/icons-material'
import { toast } from 'react-toastify'
import api from '../services/api'
import { formatLocalDateTime } from '../utils/dateUtils'

export default function AIAnalysis() {
  const [loading, setLoading] = useState(false)
  const [latestDecision, setLatestDecision] = useState<any>(null)
  const [decisions, setDecisions] = useState<any[]>([])

  useEffect(() => {
    fetchDecisions()
  }, [])

  const fetchDecisions = async () => {
    try {
      const response = await api.get('/ai/decisions')
      setDecisions(response.data.decisions || [])
      if (response.data.decisions?.length > 0) {
        setLatestDecision(response.data.decisions[0])
      }
    } catch (error) {
      console.error('Failed to fetch AI decisions:', error)
    }
  }

  const handleAnalyze = async () => {
    setLoading(true)
    try {
      const response = await api.post('/ai/analyze')
      
      setLatestDecision(response.data)
      toast.success(`AI Decision: ${response.data.decision} (${response.data.confidence}% confidence)`)
      
      // Refresh decisions list
      await fetchDecisions()
    } catch (error) {
      console.error('AI analysis failed:', error)
      toast.error('AI analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        AI Trading Analysis
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        DeepSeek AI analyzes the market and makes autonomous trading decisions
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {/* Run Analysis Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <AIIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Run AI Analysis
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                DeepSeek AI will analyze current market data and make a trading decision
              </Typography>
              <Button
                fullWidth
                variant="contained"
                color="primary"
                onClick={handleAnalyze}
                disabled={loading}
                sx={{ mt: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Analyze Market'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Latest Decision Card */}
        {latestDecision && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Latest AI Decision
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Chip
                    label={latestDecision.decision}
                    color={
                      latestDecision.decision === 'BUY'
                        ? 'success'
                        : latestDecision.decision === 'SELL'
                        ? 'error'
                        : 'default'
                    }
                    sx={{ mr: 1 }}
                  />
                  <Chip label={`${latestDecision.confidence}% confidence`} />
                  {latestDecision.executed && (
                    <Chip label="Executed" color="info" sx={{ ml: 1 }} />
                  )}
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  <strong>Reasoning:</strong> {latestDecision.reasoning}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Processing time: {latestDecision.processing_time_ms}ms
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Decision History */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Decision History
              </Typography>
              {decisions.length > 0 ? (
                <Box sx={{ mt: 2 }}>
                  {decisions.slice(0, 10).map((decision) => (
                    <Paper key={decision.id} sx={{ p: 2, mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Box>
                          <Chip
                            label={decision.decision_type}
                            size="small"
                            color={
                              decision.decision_type === 'BUY'
                                ? 'success'
                                : decision.decision_type === 'SELL'
                                ? 'error'
                                : 'default'
                            }
                            sx={{ mr: 1 }}
                          />
                          <Chip label={`${decision.confidence}%`} size="small" />
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                          {formatLocalDateTime(decision.created_at)}
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {decision.reasoning}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No AI decisions yet. Run an analysis to get started.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}







