import { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  Terminal as LogsIcon,
  History as HistoryIcon,
  Settings as EngineIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material'
import { useDispatch } from 'react-redux'
import { logout } from '../store/slices/authSlice'

const drawerWidth = 240

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Live Logs', icon: <LogsIcon />, path: '/logs' },
  { text: 'History', icon: <HistoryIcon />, path: '/history' },
  { text: 'Engine Control', icon: <EngineIcon />, path: '/engine' },
]

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const dispatch = useDispatch()

  const handleLogout = () => {
    dispatch(logout())
    navigate('/login')
  }

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
      >
        <Toolbar>
          <Box 
            sx={{ 
              bgcolor: '#000000',
              border: '4px solid #FFFFFF',
              px: 2,
              py: 0.5,
              mr: 3
            }}
          >
            <Typography 
              variant="h5" 
              component="div" 
              sx={{ 
                fontWeight: 900,
                color: '#FFFFFF',
                letterSpacing: '0.1em',
              }}
            >
              DRZR
            </Typography>
          </Box>
          <Typography 
            variant="caption" 
            component="div" 
            sx={{ 
              flexGrow: 1, 
              color: 'rgba(255, 255, 255, 0.5)',
              letterSpacing: '0.15em',
              fontWeight: 300,
              textTransform: 'uppercase',
              fontFamily: '"Inter", sans-serif'
            }}
          >
            DRAIZER V2 ARBITRAGE BOT, V.2.0.00 UNSTABLE
          </Typography>
          <IconButton 
            color="inherit" 
            onClick={handleLogout}
            sx={{ border: '2px solid #FFFFFF' }}
          >
            <LogoutIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton onClick={() => navigate(item.path)}>
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
          <Divider />
        </Box>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  )
}



