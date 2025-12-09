"""
DRAIZER V2.0 - C Engine Bridge
Python ↔ C IPC communication for monitoring & control
"""

import mmap
import struct
import socket
import os
import json
import subprocess
import signal
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path


class CEngineBridge:
    """
    Bridge between Python backend and C trading engine
    
    Communication channels:
    - Shared Memory: Read engine stats, opportunities, prices (fast, read-only)
    - Unix Socket: Send commands to engine (start/stop/config)
    """
    
    # Shared memory layout (must match C struct!)
    SHM_SIZE = 20 * 1024  # 20KB (sizeof(SharedMemory) ~17KB + margin)
    SHM_NAME = "/draizer_v2"
    SOCKET_PATH = "/tmp/draizer_v2.sock"
    
    # Struct offsets (must match C SharedMemory struct EXACTLY!)
    OFFSET_ENGINE_RUNNING = 0      # bool (1 byte)
    OFFSET_STRATEGY_ENABLED = 1    # bool[3] (3 bytes)
    # padding1[4] at offset 4
    OFFSET_OPPS_DETECTED = 8       # uint64_t (8 bytes)
    OFFSET_OPPS_EXECUTED = 16      # uint64_t (8 bytes)
    OFFSET_ORDERS_PLACED = 24      # uint64_t (8 bytes)
    OFFSET_ORDERS_FILLED = 32      # uint64_t (8 bytes)
    OFFSET_TOTAL_PROFIT = 40       # double (8 bytes) ← FIXED!
    OFFSET_BALANCE = 48            # double (8 bytes)
    OFFSET_WINS = 56               # uint32_t (4 bytes)
    OFFSET_LOSSES = 60             # uint32_t (4 bytes)
    OFFSET_WIN_RATE = 64           # double (8 bytes)
    OFFSET_OPEN_POSITIONS = 72     # uint32_t (4 bytes)
    # padding2[4] at offset 76
    OFFSET_AVG_LATENCY = 80        # uint32_t (4 bytes) ← FIXED!
    OFFSET_P99_LATENCY = 84        # uint32_t (4 bytes)
    OFFSET_LAST_UPDATE = 88        # uint64_t (8 bytes)
    
    def __init__(self):
        self.shm: Optional[mmap.mmap] = None
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.engine_process: Optional[subprocess.Popen] = None
        self.engine_path = Path(__file__).parent.parent.parent / "c_engine" / "build" / "draizer_engine"
    
    def connect(self) -> bool:
        """
        Connect to C engine via shared memory
        
        Returns:
            True if successful
        """
        try:
            # Open shared memory
            shm_path = f"/dev/shm{self.SHM_NAME}"
            
            if not os.path.exists(shm_path):
                print(f"⚠️  C engine not running (shared memory not found)")
                return False
            
            # Get real file size
            fd = os.open(shm_path, os.O_RDONLY)
            file_size = os.fstat(fd).st_size
            
            # Use actual file size, not hardcoded constant
            self.shm = mmap.mmap(fd, file_size, access=mmap.ACCESS_READ)
            os.close(fd)
            
            self.connected = True
            print(f"✅ Connected to C engine")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to C engine: {e}")
            return False
    
    def disconnect(self):
        """Close connections"""
        if self.shm:
            self.shm.close()
            self.shm = None
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        self.connected = False
    
    def get_stats(self) -> Optional[Dict]:
        """
        Read current engine statistics from shared memory
        
        Returns:
            Dict with stats or None if not connected
        """
        if not self.connected or not self.shm:
            return None
        
        try:
            # Read all fields from shared memory (packed struct - FIXED OFFSETS!)
            engine_running = struct.unpack_from('?', self.shm, self.OFFSET_ENGINE_RUNNING)[0]
            opps_detected = struct.unpack_from('Q', self.shm, self.OFFSET_OPPS_DETECTED)[0]
            opps_executed = struct.unpack_from('Q', self.shm, self.OFFSET_OPPS_EXECUTED)[0]
            orders_placed = struct.unpack_from('Q', self.shm, self.OFFSET_ORDERS_PLACED)[0]
            orders_filled = struct.unpack_from('Q', self.shm, self.OFFSET_ORDERS_FILLED)[0]
            total_profit = struct.unpack_from('d', self.shm, self.OFFSET_TOTAL_PROFIT)[0]
            balance = struct.unpack_from('d', self.shm, self.OFFSET_BALANCE)[0]
            wins = struct.unpack_from('I', self.shm, self.OFFSET_WINS)[0]
            losses = struct.unpack_from('I', self.shm, self.OFFSET_LOSSES)[0]
            win_rate = struct.unpack_from('d', self.shm, self.OFFSET_WIN_RATE)[0]
            open_positions = struct.unpack_from('I', self.shm, self.OFFSET_OPEN_POSITIONS)[0]
            avg_latency_us = struct.unpack_from('I', self.shm, self.OFFSET_AVG_LATENCY)[0]
            p99_latency_us = struct.unpack_from('I', self.shm, self.OFFSET_P99_LATENCY)[0]
            last_update_ns = struct.unpack_from('Q', self.shm, self.OFFSET_LAST_UPDATE)[0]
            
            return {
                'engine_running': engine_running,
                'opportunities_detected': opps_detected,
                'opportunities_executed': opps_executed,
                'orders_placed': orders_placed,
                'orders_filled': orders_filled,
                'total_profit_usd': total_profit,
                'balance_usd': balance,
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'open_positions': open_positions,
                'avg_latency_us': avg_latency_us,
                'p99_latency_us': p99_latency_us,
                'success_rate': (opps_executed / opps_detected * 100) if opps_detected > 0 else 0,
                'fill_rate': (orders_filled / orders_placed * 100) if orders_placed > 0 else 0,
                'last_update_ns': last_update_ns,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"❌ Error reading stats: {e}")
            return None
    
    def get_operations(self, limit: int = 100) -> List[Dict]:
        """
        Read operations from shared memory ring buffer
        
        Args:
            limit: Max number of operations to return
        
        Returns:
            List of operation dicts
        """
        if not self.connected or not self.shm:
            return []
        
        operations = []
        
        try:
            # Calculate offsets for operations ring buffer
            # SharedMemory struct layout (see shared_memory.h):
            # - 96 bytes for stats
            # - 100 operations @ 176 bytes each = 17,600 bytes
            # - operations_head at offset 17,696
            # - operations_tail at offset 17,700
            # - total_operations at offset 17,704
            
            operations_start_offset = 96
            operation_size = 176  # sizeof(ShmOperation)
            operations_head_offset = 17696
            operations_tail_offset = 17700
            
            # Read head and tail pointers
            head = struct.unpack_from('I', self.shm, operations_head_offset)[0]
            tail = struct.unpack_from('I', self.shm, operations_tail_offset)[0]
            
            # Read operations from tail to head (circular buffer)
            count = 0
            idx = tail
            while idx != head and count < limit:
                # Read operation from shared memory
                offset = operations_start_offset + (idx * operation_size)
                
                op_id = struct.unpack_from('Q', self.shm, offset)[0]
                timestamp_ns = struct.unpack_from('Q', self.shm, offset + 8)[0]
                op_type = struct.unpack_from('20s', self.shm, offset + 16)[0].decode('utf-8').rstrip('\x00')
                strategy = struct.unpack_from('20s', self.shm, offset + 36)[0].decode('utf-8').rstrip('\x00')
                symbol = struct.unpack_from('12s', self.shm, offset + 56)[0].decode('utf-8').rstrip('\x00')
                exchange_buy = struct.unpack_from('20s', self.shm, offset + 68)[0].decode('utf-8').rstrip('\x00')
                exchange_sell = struct.unpack_from('20s', self.shm, offset + 88)[0].decode('utf-8').rstrip('\x00')
                quantity = struct.unpack_from('d', self.shm, offset + 108)[0]
                entry_price = struct.unpack_from('d', self.shm, offset + 116)[0]
                exit_price = struct.unpack_from('d', self.shm, offset + 124)[0]
                pnl = struct.unpack_from('d', self.shm, offset + 132)[0]
                pnl_percent = struct.unpack_from('d', self.shm, offset + 140)[0]
                spread_bps = struct.unpack_from('d', self.shm, offset + 148)[0]
                fees_paid = struct.unpack_from('d', self.shm, offset + 156)[0]
                is_open = struct.unpack_from('?', self.shm, offset + 164)[0]
                
                operations.append({
                    'id': op_id,
                    'timestamp': timestamp_ns // 1_000_000,  # Convert to milliseconds
                    'type': op_type,
                    'strategy': strategy,
                    'symbol': symbol,
                    'exchange_buy': exchange_buy,
                    'exchange_sell': exchange_sell,
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'spread_bps': spread_bps,
                    'fees_paid': fees_paid,
                    'is_open': is_open
                })
                
                idx = (idx + 1) % 100  # Ring buffer size
                count += 1
            
            # Update tail pointer in shared memory (mark as read)
            struct.pack_into('I', self.shm, operations_tail_offset, head)
        
        except Exception as e:
            print(f"❌ Error reading operations: {e}")
        
        return operations
    
    def get_latest_opportunities(self, limit: int = 10) -> List[Dict]:
        """
        Read latest detected opportunities from shared memory
        
        Args:
            limit: Max number of opportunities to return
        
        Returns:
            List of opportunity dicts
        """
        if not self.connected or not self.shm:
            return []
        
        opportunities = []
        
        try:
            # TODO: Read from opportunity ring buffer in shared memory
            # For now, return empty list (to be implemented)
            pass
        
        except Exception as e:
            print(f"❌ Error reading opportunities: {e}")
        
        return opportunities
    
    def get_latest_prices(self, limit: int = 10) -> List[Dict]:
        """
        Read latest prices from shared memory
        
        Args:
            limit: Max number of prices to return
        
        Returns:
            List of price dicts
        """
        if not self.connected or not self.shm:
            return []
        
        prices = []
        
        try:
            # TODO: Read from price ring buffer in shared memory
            # For now, return empty list (to be implemented)
            pass
        
        except Exception as e:
            print(f"❌ Error reading prices: {e}")
        
        return prices
    
    def send_command(self, command: str, data: str = "") -> bool:
        """
        Send command to C engine via Unix socket
        
        Args:
            command: Command type ("start", "stop", "update_config", "shutdown")
            data: Optional command data (JSON string)
        
        Returns:
            True if successful
        """
        try:
            # Connect to Unix socket
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.SOCKET_PATH)
            
            # Command mapping
            commands = {
                'start': 0,
                'stop': 1,
                'update_config': 2,
                'shutdown': 3
            }
            
            cmd_type = commands.get(command, 0)
            
            # Pack command (4 bytes type + 256 bytes data)
            cmd_bytes = struct.pack('I256s', cmd_type, data.encode()[:256])
            sock.send(cmd_bytes)
            
            sock.close()
            
            print(f"✅ Sent command: {command}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to send command: {e}")
            return False
    
    def start_strategy(self, strategy_name: str) -> bool:
        """
        Start a specific strategy in C engine
        
        Args:
            strategy_name: "cross_exchange", "funding_rate", "triangular"
        
        Returns:
            True if successful
        """
        data = json.dumps({'strategy': strategy_name})
        return self.send_command('start', data)
    
    def stop_strategy(self, strategy_name: str) -> bool:
        """Stop a specific strategy"""
        data = json.dumps({'strategy': strategy_name})
        return self.send_command('stop', data)
    
    def update_config(self, config: Dict) -> bool:
        """
        Hot-reload configuration in C engine
        
        Args:
            config: New configuration dict
        
        Returns:
            True if successful
        """
        data = json.dumps(config)
        return self.send_command('update_config', data)
    
    def shutdown(self) -> bool:
        """Gracefully shutdown C engine"""
        return self.send_command('shutdown')
    
    def is_running(self) -> bool:
        """Check if C engine is running"""
        if not self.connected:
            return False
        
        stats = self.get_stats()
        return stats['engine_running'] if stats else False
    
    def get_performance_metrics(self) -> Dict:
        """
        Calculate performance metrics from stats
        
        Returns:
            Dict with derived metrics
        """
        stats = self.get_stats()
        
        if not stats:
            return {}
        
        return {
            'latency_p50_us': stats['avg_latency_us'],
            'latency_p99_us': stats['p99_latency_us'],
            'throughput_ops_per_sec': stats['opportunities_detected'] / 3600,  # Assuming 1 hour
            'success_rate_pct': stats['success_rate'],
            'fill_rate_pct': stats['fill_rate'],
            'total_profit_usd': stats['total_profit_usd'],
            'profit_per_trade': stats['total_profit_usd'] / stats['opportunities_executed'] if stats['opportunities_executed'] > 0 else 0
        }
    
    def health_check(self) -> Dict:
        """
        Comprehensive health check
        
        Returns:
            Health status dict
        """
        if not self.connected:
            return {
                'status': 'disconnected',
                'healthy': False,
                'message': 'Not connected to C engine'
            }
        
        stats = self.get_stats()
        
        if not stats or not stats['engine_running']:
            return {
                'status': 'stopped',
                'healthy': False,
                'message': 'C engine not running'
            }
        
        # Check latency
        if stats['p99_latency_us'] > 200:  # >200μs is bad
            return {
                'status': 'degraded',
                'healthy': False,
                'message': f"High latency: P99={stats['p99_latency_us']}μs"
            }
        
        # Check success rate
        if stats['success_rate'] < 30 and stats['opportunities_detected'] > 10:
            return {
                'status': 'degraded',
                'healthy': False,
                'message': f"Low success rate: {stats['success_rate']:.1f}%"
            }
        
        return {
            'status': 'healthy',
            'healthy': True,
            'message': 'All systems operational',
            'stats': stats
        }
    
    def start_engine(self) -> bool:
        """
        Start C engine process
        
        Returns:
            True if started successfully
        """
        if self.is_engine_process_running():
            print("⚠️  Engine already running")
            return True
        
        try:
            # Check if binary exists
            if not self.engine_path.exists():
                print(f"❌ Engine binary not found: {self.engine_path}")
                print(f"   Build it first: cd backend/c_engine/build && cmake .. && make")
                return False
            
            # Start engine in background
            config_path = self.engine_path.parent.parent / "config" / "engine.json"
            
            self.engine_process = subprocess.Popen(
                [str(self.engine_path), "--config", str(config_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.engine_path.parent)
            )
            
            print(f"✅ C engine started (PID: {self.engine_process.pid})")
            
            # Wait a moment for shared memory to be created
            import time
            time.sleep(1)
            
            # Connect to shared memory
            self.connect()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start engine: {e}")
            return False
    
    def stop_engine(self) -> bool:
        """
        Stop C engine process gracefully
        
        Returns:
            True if stopped successfully
        """
        if not self.is_engine_process_running():
            print("⚠️  Engine not running")
            return True
        
        try:
            if self.engine_process:
                # Send SIGTERM for graceful shutdown
                self.engine_process.terminate()
                
                # Wait up to 5 seconds
                try:
                    self.engine_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if not responding
                    print("⚠️  Engine not responding, forcing shutdown...")
                    self.engine_process.kill()
                    self.engine_process.wait()
                
                self.engine_process = None
                print("✅ Engine stopped")
            
            self.disconnect()
            return True
            
        except Exception as e:
            print(f"❌ Failed to stop engine: {e}")
            return False
    
    def restart_engine(self) -> bool:
        """
        Restart C engine
        
        Returns:
            True if restarted successfully
        """
        print("🔄 Restarting engine...")
        
        if not self.stop_engine():
            return False
        
        import time
        time.sleep(1)  # Wait for cleanup
        
        return self.start_engine()
    
    def is_engine_process_running(self) -> bool:
        """Check if engine process is running"""
        if self.engine_process is None:
            return False
        
        # Check if process is still alive
        return self.engine_process.poll() is None


# Example usage:
"""
# In FastAPI endpoint
from app.services.c_engine_bridge import CEngineBridge

bridge = CEngineBridge()

# Connect
if bridge.connect():
    # Get stats
    stats = bridge.get_stats()
    print(f"Opportunities detected: {stats['opportunities_detected']}")
    print(f"Total profit: ${stats['total_profit_usd']:.2f}")
    print(f"P99 latency: {stats['p99_latency_us']}μs")
    
    # Start strategy
    bridge.start_strategy("cross_exchange")
    
    # Health check
    health = bridge.health_check()
    print(f"Status: {health['status']}")
    
    # Disconnect
    bridge.disconnect()
"""

