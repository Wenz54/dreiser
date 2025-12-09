import { Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@mui/material'

import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import ArbitrageDashboard from './pages/ArbitrageDashboard'
import ArbitrageLogs from './pages/ArbitrageLogs'
import ArbitrageHistory from './pages/ArbitrageHistory'
import EngineControl from './pages/EngineControl'
import { useAuth } from './hooks/useAuth'

function App() {
  const { isAuthenticated } = useAuth()

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected routes */}
        <Route
          path="/*"
          element={
            isAuthenticated ? (
              <Layout>
                <Routes>
                  <Route path="/" element={<ArbitrageDashboard />} />
                  <Route path="/logs" element={<ArbitrageLogs />} />
                  <Route path="/history" element={<ArbitrageHistory />} />
                  <Route path="/engine" element={<EngineControl />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Layout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </Box>
  )
}

export default App

