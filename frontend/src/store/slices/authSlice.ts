import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface AuthState {
  isAuthenticated: boolean
  accessToken: string | null
  user: {
    id: string
    username: string
    email: string
  } | null
}

const initialState: AuthState = {
  isAuthenticated: !!localStorage.getItem('accessToken'),
  accessToken: localStorage.getItem('accessToken'),
  user: null,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (
      state,
      action: PayloadAction<{ accessToken: string; refreshToken: string; user: any }>
    ) => {
      state.accessToken = action.payload.accessToken
      state.isAuthenticated = true
      state.user = action.payload.user
      localStorage.setItem('accessToken', action.payload.accessToken)
      localStorage.setItem('refreshToken', action.payload.refreshToken)
    },
    logout: (state) => {
      state.isAuthenticated = false
      state.accessToken = null
      state.user = null
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
    },
  },
})

export const { setCredentials, logout } = authSlice.actions
export default authSlice.reducer












