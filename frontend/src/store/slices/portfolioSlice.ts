import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface PortfolioState {
  balance: number
  totalPnL: number
  totalTrades: number
  winRate: number
  loading: boolean
}

const initialState: PortfolioState = {
  balance: 0,
  totalPnL: 0,
  totalTrades: 0,
  winRate: 0,
  loading: false,
}

const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    setPortfolio: (state, action: PayloadAction<Partial<PortfolioState>>) => {
      return { ...state, ...action.payload }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
  },
})

export const { setPortfolio, setLoading } = portfolioSlice.actions
export default portfolioSlice.reducer












