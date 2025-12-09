"""
DRAIZER V2.0 - Strategy Optimizer
Parameter optimization using grid search / genetic algorithms
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Callable
from itertools import product
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

from app.services.backtest_service import BacktestService


class StrategyOptimizer:
    """
    Optimize strategy parameters using backtesting
    
    Methods:
    - Grid search: Test all parameter combinations
    - Random search: Sample parameter space randomly
    - Genetic algorithm: Evolve best parameters (future)
    """
    
    def __init__(self, backtest_service: BacktestService):
        self.backtest = backtest_service
    
    def grid_search(
        self,
        strategy: str,
        symbols: List[str],
        exchanges: List[str],
        param_grid: Dict[str, List],
        start_date: datetime,
        end_date: datetime,
        metric: str = "sharpe_ratio",
        parallel: bool = True
    ) -> Tuple[Dict, pd.DataFrame]:
        """
        Grid search optimization
        
        Args:
            strategy: Strategy name
            symbols: Trading pairs
            exchanges: Exchanges to test
            param_grid: Dict of parameter name → list of values
                Example: {
                    'min_spread_bps': [50, 75, 100, 125],
                    'max_position_usd': [300, 500, 700],
                    'capital_usd': [10000]
                }
            start_date: Backtest start
            end_date: Backtest end
            metric: Metric to optimize ("sharpe_ratio", "roi", "total_pnl")
            parallel: Use parallel processing
        
        Returns:
            (best_params, results_dataframe)
        """
        # Generate all combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))
        
        print(f"🔍 Grid search: testing {len(combinations)} combinations...")
        
        results = []
        
        if parallel:
            # Parallel execution (faster)
            with ProcessPoolExecutor() as executor:
                futures = []
                for combo in combinations:
                    params = dict(zip(param_names, combo))
                    future = executor.submit(
                        self._run_single_backtest,
                        strategy, symbols, exchanges, start_date, end_date, params
                    )
                    futures.append((params, future))
                
                for params, future in futures:
                    result = future.result()
                    results.append({
                        **params,
                        **result
                    })
        else:
            # Sequential execution
            for i, combo in enumerate(combinations, 1):
                params = dict(zip(param_names, combo))
                print(f"   [{i}/{len(combinations)}] Testing {params}...")
                
                result = self._run_single_backtest(
                    strategy, symbols, exchanges, start_date, end_date, params
                )
                
                results.append({
                    **params,
                    **result
                })
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Find best params
        best_idx = df[metric].idxmax()
        best_params = df.loc[best_idx, param_names].to_dict()
        best_score = df.loc[best_idx, metric]
        
        print(f"\n✅ Best parameters found:")
        for param, value in best_params.items():
            print(f"   {param}: {value}")
        print(f"   {metric}: {best_score:.2f}")
        
        return best_params, df
    
    def _run_single_backtest(
        self,
        strategy: str,
        symbols: List[str],
        exchanges: List[str],
        start_date: datetime,
        end_date: datetime,
        params: Dict
    ) -> Dict:
        """
        Run single backtest (internal helper)
        """
        try:
            # Note: This would need async handling in real implementation
            # For now, simplified
            result = self.backtest.run_backtest(
                strategy=strategy,
                symbols=symbols,
                exchanges=exchanges,
                start_date=start_date,
                end_date=end_date,
                params=params
            )
            return result
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            return {
                'num_trades': 0,
                'total_pnl': 0,
                'roi': 0,
                'sharpe_ratio': 0,
                'win_rate': 0,
                'max_drawdown': 0
            }
    
    def random_search(
        self,
        strategy: str,
        symbols: List[str],
        exchanges: List[str],
        param_ranges: Dict[str, Tuple],
        start_date: datetime,
        end_date: datetime,
        n_iterations: int = 50,
        metric: str = "sharpe_ratio"
    ) -> Tuple[Dict, pd.DataFrame]:
        """
        Random search optimization (faster than grid search)
        
        Args:
            param_ranges: Dict of parameter name → (min, max)
                Example: {
                    'min_spread_bps': (50, 150),
                    'max_position_usd': (200, 1000),
                    'capital_usd': (10000, 10000)  # Fixed value
                }
            n_iterations: Number of random samples to test
        
        Returns:
            (best_params, results_dataframe)
        """
        print(f"🎲 Random search: testing {n_iterations} random combinations...")
        
        results = []
        
        for i in range(n_iterations):
            # Sample random parameters
            params = {}
            for param_name, (min_val, max_val) in param_ranges.items():
                if min_val == max_val:
                    params[param_name] = min_val
                elif isinstance(min_val, int):
                    params[param_name] = np.random.randint(min_val, max_val + 1)
                else:
                    params[param_name] = np.random.uniform(min_val, max_val)
            
            print(f"   [{i+1}/{n_iterations}] Testing {params}...")
            
            result = self._run_single_backtest(
                strategy, symbols, exchanges, start_date, end_date, params
            )
            
            results.append({
                **params,
                **result
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Find best params
        best_idx = df[metric].idxmax()
        best_params = df.loc[best_idx, list(param_ranges.keys())].to_dict()
        best_score = df.loc[best_idx, metric]
        
        print(f"\n✅ Best parameters found:")
        for param, value in best_params.items():
            print(f"   {param}: {value}")
        print(f"   {metric}: {best_score:.2f}")
        
        return best_params, df
    
    def walk_forward_optimization(
        self,
        strategy: str,
        symbols: List[str],
        exchanges: List[str],
        param_grid: Dict[str, List],
        total_days: int = 30,
        train_days: int = 21,
        test_days: int = 7,
        metric: str = "sharpe_ratio"
    ) -> Dict:
        """
        Walk-forward optimization (prevent overfitting)
        
        Process:
        1. Split data into train/test windows
        2. Optimize on train window
        3. Validate on test window
        4. Move window forward
        5. Repeat
        
        Args:
            total_days: Total period to test
            train_days: Training window size
            test_days: Testing window size
        
        Returns:
            Results with out-of-sample performance
        """
        print(f"🚶 Walk-forward optimization:")
        print(f"   Total: {total_days} days")
        print(f"   Train: {train_days} days, Test: {test_days} days")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=total_days)
        
        results = []
        current_date = start_date
        
        while current_date + timedelta(days=train_days + test_days) <= end_date:
            train_start = current_date
            train_end = current_date + timedelta(days=train_days)
            test_start = train_end
            test_end = test_start + timedelta(days=test_days)
            
            print(f"\n📅 Window: {train_start.date()} → {test_end.date()}")
            
            # Optimize on training data
            print("   Training...")
            best_params, _ = self.grid_search(
                strategy=strategy,
                symbols=symbols,
                exchanges=exchanges,
                param_grid=param_grid,
                start_date=train_start,
                end_date=train_end,
                metric=metric,
                parallel=True
            )
            
            # Validate on test data
            print("   Testing...")
            test_result = self._run_single_backtest(
                strategy, symbols, exchanges, test_start, test_end, best_params
            )
            
            results.append({
                'train_start': train_start,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end,
                'best_params': best_params,
                'test_sharpe': test_result['sharpe_ratio'],
                'test_roi': test_result['roi'],
                'test_trades': test_result['num_trades']
            })
            
            # Move window forward
            current_date += timedelta(days=test_days)
        
        # Aggregate results
        test_sharpes = [r['test_sharpe'] for r in results]
        avg_sharpe = np.mean(test_sharpes)
        std_sharpe = np.std(test_sharpes)
        
        print(f"\n📊 Walk-forward results:")
        print(f"   Average Sharpe (out-of-sample): {avg_sharpe:.2f} ± {std_sharpe:.2f}")
        print(f"   Stability: {'✅ Good' if std_sharpe < 0.5 else '⚠️ Unstable'}")
        
        return {
            'windows': results,
            'avg_sharpe': avg_sharpe,
            'std_sharpe': std_sharpe
        }


# Example usage:
"""
optimizer = StrategyOptimizer(backtest_service)

# Grid search
best_params, results = optimizer.grid_search(
    strategy="cross_exchange",
    symbols=["BTCUSDT"],
    exchanges=["binance", "mexc"],
    param_grid={
        'min_spread_bps': [50, 75, 100, 125, 150],
        'max_position_usd': [300, 500, 700],
        'capital_usd': [10000]
    },
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now(),
    metric="sharpe_ratio"
)

# Output:
# 🔍 Grid search: testing 15 combinations...
# ✅ Best parameters found:
#    min_spread_bps: 75
#    max_position_usd: 500
#    sharpe_ratio: 2.14

# Save best config to C engine
with open('backend/c_engine/config/strategies.json', 'w') as f:
    json.dump({
        'strategies': [{
            'name': 'cross_exchange',
            'enabled': True,
            'params': best_params
        }]
    }, f, indent=2)
"""


