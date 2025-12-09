import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import portfolioReducer from './slices/portfolioSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    portfolio: portfolioReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch












