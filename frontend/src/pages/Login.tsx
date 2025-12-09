import { useState } from 'react'
import { useNavigate, Link as RouterLink } from 'react-router-dom'
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Link,
} from '@mui/material'
import { useDispatch } from 'react-redux'
import { toast } from 'react-toastify'
import api from '../services/api'
import { setCredentials } from '../store/slices/authSlice'

export default function Login() {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [mfaCode, setMfaCode] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await api.post('/auth/login', {
        username,
        password,
        mfa_code: mfaCode || null,
      })

      dispatch(setCredentials({
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
        user: null, // TODO: Get user info
      }))

      toast.success('Login successful!')
      navigate('/')
    } catch (error: any) {
      console.error('Login failed:', error)
      const errorMsg = error.response?.data?.detail || 'Login failed. Please check your credentials.'
      toast.error(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={6} sx={{ p: 4, borderRadius: 3 }}>
          <Typography component="h1" variant="h4" align="center" gutterBottom>
            🚀 Draizer AI
          </Typography>
          <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 3 }}>
            AI-Powered Trading Platform
          </Typography>

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Username"
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <TextField
              margin="normal"
              fullWidth
              name="mfaCode"
              label="2FA Code (if enabled)"
              id="mfaCode"
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? 'Logging in...' : 'Login'}
            </Button>
            <Box sx={{ textAlign: 'center' }}>
              <Link component={RouterLink} to="/register" variant="body2">
                {"Don't have an account? Sign Up"}
              </Link>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}

