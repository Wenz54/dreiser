import { createTheme } from '@mui/material/styles'

// 🎨 ELITE MONOCHROME THEME
// Inspired by: Bloomberg Terminal × Porsche Design × Swiss Banking
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#FFFFFF',
      light: '#F5F5F5',
      dark: '#E0E0E0',
      contrastText: '#000000',
    },
    secondary: {
      main: '#1A1A1A',
      light: '#2A2A2A',
      dark: '#0A0A0A',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#000000',
      paper: '#0A0A0A',
    },
    text: {
      primary: '#FFFFFF',
      secondary: '#A0A0A0',
      disabled: '#505050',
    },
    success: {
      main: '#FFFFFF',
      light: '#F5F5F5',
      dark: '#CCCCCC',
    },
    error: {
      main: '#FFFFFF',
      light: '#F5F5F5',
      dark: '#CCCCCC',
    },
    warning: {
      main: '#E0E0E0',
    },
    info: {
      main: '#B0B0B0',
    },
    divider: 'rgba(255, 255, 255, 0.08)',
  },
  typography: {
    fontFamily: '"Inter", "Helvetica Neue", "Arial", -apple-system, system-ui, sans-serif',
    fontWeightLight: 300,
    fontWeightRegular: 400,
    fontWeightMedium: 500,
    fontWeightBold: 600,
    h1: {
      fontSize: '3rem',
      fontWeight: 300,
      letterSpacing: '-0.03em',
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2.5rem',
      fontWeight: 300,
      letterSpacing: '-0.02em',
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '2rem',
      fontWeight: 400,
      letterSpacing: '-0.01em',
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.75rem',
      fontWeight: 400,
      letterSpacing: '-0.01em',
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.5rem',
      fontWeight: 500,
      letterSpacing: '0em',
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1.25rem',
      fontWeight: 500,
      letterSpacing: '0.01em',
      lineHeight: 1.5,
    },
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 400,
      letterSpacing: '0.02em',
      lineHeight: 1.6,
    },
    body1: {
      fontSize: '0.95rem',
      fontWeight: 400,
      letterSpacing: '0.01em',
      lineHeight: 1.7,
    },
    body2: {
      fontSize: '0.875rem',
      fontWeight: 400,
      letterSpacing: '0.01em',
      lineHeight: 1.6,
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 500,
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
    },
    caption: {
      fontSize: '0.75rem',
      fontWeight: 400,
      letterSpacing: '0.05em',
      lineHeight: 1.5,
    },
    overline: {
      fontSize: '0.75rem',
      fontWeight: 600,
      letterSpacing: '0.15em',
      textTransform: 'uppercase',
      lineHeight: 2,
    },
  },
  shape: {
    borderRadius: 0,
  },
  spacing: 8,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundImage: 'radial-gradient(circle at 50% 50%, #0A0A0A 0%, #000000 100%)',
          backgroundAttachment: 'fixed',
        },
        '@global': {
          '*::-webkit-scrollbar': {
            width: '8px',
            height: '8px',
          },
          '*::-webkit-scrollbar-track': {
            background: '#0A0A0A',
          },
          '*::-webkit-scrollbar-thumb': {
            background: '#333333',
            border: '1px solid #1A1A1A',
          },
          '*::-webkit-scrollbar-thumb:hover': {
            background: '#4A4A4A',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'uppercase',
          fontWeight: 500,
          letterSpacing: '0.08em',
          borderRadius: 0,
          padding: '10px 24px',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          '&:hover': {
            border: '1px solid rgba(255, 255, 255, 0.8)',
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            transform: 'translateY(-1px)',
          },
        },
        contained: {
          backgroundColor: '#FFFFFF',
          color: '#000000',
          border: '1px solid #FFFFFF',
          boxShadow: '0 2px 8px rgba(255, 255, 255, 0.1)',
          '&:hover': {
            backgroundColor: '#F0F0F0',
            boxShadow: '0 4px 16px rgba(255, 255, 255, 0.2)',
          },
        },
        outlined: {
          border: '1px solid rgba(255, 255, 255, 0.3)',
          '&:hover': {
            border: '1px solid rgba(255, 255, 255, 0.8)',
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
          },
        },
        text: {
          border: 'none',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: 'rgba(10, 10, 10, 0.8)',
          backdropFilter: 'blur(10px)',
          borderRadius: 0,
          border: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: '0 4px 24px rgba(0, 0, 0, 0.5)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            border: '1px solid rgba(255, 255, 255, 0.15)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.7)',
            transform: 'translateY(-2px)',
          },
        },
      },
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: '32px',
          '&:last-child': {
            paddingBottom: '32px',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(0, 0, 0, 0.95)',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: '0 2px 16px rgba(0, 0, 0, 0.8)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#000000',
          borderRight: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: '2px 0 16px rgba(0, 0, 0, 0.8)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: 'rgba(10, 10, 10, 0.9)',
          borderRadius: 0,
        },
        outlined: {
          border: '1px solid rgba(255, 255, 255, 0.08)',
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: 'rgba(255, 255, 255, 0.08)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 0,
            '& fieldset': {
              borderColor: 'rgba(255, 255, 255, 0.2)',
              transition: 'border-color 0.2s',
            },
            '&:hover fieldset': {
              borderColor: 'rgba(255, 255, 255, 0.4)',
            },
            '&.Mui-focused fieldset': {
              borderColor: 'rgba(255, 255, 255, 0.8)',
              borderWidth: '1px',
            },
          },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 0,
          border: '1px solid rgba(255, 255, 255, 0.2)',
          backgroundColor: 'rgba(10, 10, 10, 0.9)',
        },
        standardInfo: {
          backgroundColor: 'rgba(176, 176, 176, 0.1)',
          color: '#FFFFFF',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 0,
          border: '1px solid rgba(255, 255, 255, 0.2)',
          fontWeight: 500,
          letterSpacing: '0.05em',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
          fontVariantNumeric: 'tabular-nums',
        },
        head: {
          fontWeight: 600,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          fontSize: '0.75rem',
        },
      },
    },
  },
})

export default theme



