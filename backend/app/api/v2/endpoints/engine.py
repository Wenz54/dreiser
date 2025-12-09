"""
DRAIZER V2 API - C Engine Management
Monitor and control C trading engine
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Optional
import asyncio
import json
import time

from app.api.deps import get_current_user, get_db
from app.services.c_engine_bridge import CEngineBridge
from app.models.user import User

router = APIRouter()

# Global bridge instance (singleton)
_bridge = None

def get_bridge() -> CEngineBridge:
    """Get or create C engine bridge"""
    global _bridge
    if _bridge is None:
        _bridge = CEngineBridge()
        _bridge.connect()
    return _bridge


@router.get("/status")
async def get_engine_status(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get C engine status
    
    Returns:
        Engine running status, stats, health
    """
    bridge = get_bridge()
    
    if not bridge.connected:
        return {
            'running': False,
            'uptime_seconds': 0,
            'connected_exchanges': [],
            'active_positions': 0,
            'pending_orders': 0,
            'message': 'C engine not running'
        }
    
    stats = bridge.get_stats()
    
    if not stats:
        return {
            'running': False,
            'uptime_seconds': 0,
            'connected_exchanges': [],
            'active_positions': 0,
            'pending_orders': 0,
            'message': 'Failed to read engine stats'
        }
    
    # Return flat structure matching frontend EngineStatus interface
    return {
        'running': stats.get('engine_running', False),
        'uptime_seconds': 0,  # TODO: calculate from last_update_ns
        'connected_exchanges': [],  # TODO: read from engine
        'active_positions': stats.get('open_positions', 0),
        'pending_orders': 0,  # TODO: read from engine
        'balance_usd': stats.get('balance_usd', 0),
        'total_profit_usd': stats.get('total_profit_usd', 0),
        'wins': stats.get('wins', 0),
        'losses': stats.get('losses', 0),
        'win_rate': stats.get('win_rate', 0),
        'avg_latency_us': stats.get('avg_latency_us', 0),
        'p99_latency_us': stats.get('p99_latency_us', 0)
    }


@router.get("/stats")
async def get_engine_stats(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get detailed engine statistics
    
    Returns:
        Opportunities, orders, profit, latency
    """
    bridge = get_bridge()
    
    stats = bridge.get_stats()
    if not stats:
        raise HTTPException(status_code=503, detail="C engine not available")
    
    return stats


@router.get("/performance")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get performance metrics
    
    Returns:
        Derived metrics: throughput, success rate, profit per trade
    """
    bridge = get_bridge()
    
    metrics = bridge.get_performance_metrics()
    if not metrics:
        raise HTTPException(status_code=503, detail="C engine not available")
    
    return metrics


@router.post("/strategy/{strategy_name}/start")
async def start_strategy(
    strategy_name: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Start a specific strategy
    
    Args:
        strategy_name: "cross_exchange", "funding_rate", "triangular"
    
    Returns:
        Success status
    """
    bridge = get_bridge()
    
    if strategy_name not in ["cross_exchange", "funding_rate", "triangular"]:
        raise HTTPException(status_code=400, detail="Invalid strategy name")
    
    success = bridge.start_strategy(strategy_name)
    
    if not success:
        raise HTTPException(status_code=503, detail="Failed to start strategy")
    
    return {
        'success': True,
        'strategy': strategy_name,
        'status': 'started'
    }


@router.post("/strategy/{strategy_name}/stop")
async def stop_strategy(
    strategy_name: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Stop a specific strategy"""
    bridge = get_bridge()
    
    success = bridge.stop_strategy(strategy_name)
    
    if not success:
        raise HTTPException(status_code=503, detail="Failed to stop strategy")
    
    return {
        'success': True,
        'strategy': strategy_name,
        'status': 'stopped'
    }


@router.post("/config/update")
async def update_config(
    config: Dict,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Hot-reload configuration
    
    Args:
        config: New configuration dict
    
    Returns:
        Success status
    """
    bridge = get_bridge()
    
    success = bridge.update_config(config)
    
    if not success:
        raise HTTPException(status_code=503, detail="Failed to update config")
    
    return {
        'success': True,
        'message': 'Configuration updated'
    }


@router.post("/start")
async def start_engine(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Start C engine container via Docker API
    
    Returns:
        Success status
    """
    import docker
    import os
    import time
    
    # Check if already running
    shm_path = "/dev/shm/draizer_v2"
    
    if os.path.exists(shm_path):
        return {
            'success': True,
            'message': '✅ C engine is already running'
        }
    
    # Start container via Docker API
    try:
        # Connect to Docker
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        
        # Get container
        container = client.containers.get('draizer_c_engine')
        
        # Check if already running
        container.reload()
        if container.status == 'running':
            return {
                'success': True,
                'message': '✅ C engine is already running'
            }
        
        # Start container
        container.start()
        
        # Wait up to 10 seconds for engine to initialize
        for i in range(10):
            time.sleep(1)
            if os.path.exists(shm_path):
                break
        
        # Verify it started
        if os.path.exists(shm_path):
            # Force bridge to reconnect to new shared memory
            bridge = get_bridge()
            bridge.disconnect()
            bridge.connect()
            
            return {
                'success': True,
                'message': '✅ C engine started successfully'
            }
        else:
            raise HTTPException(
                status_code=503,
                detail="Container started but shared memory not initialized"
            )
            
    except docker.errors.NotFound:
        raise HTTPException(
            status_code=503,
            detail="C engine container not found. Run: docker-compose up -d c_engine"
        )
    except docker.errors.APIError as e:
        raise HTTPException(status_code=503, detail=f"Docker API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to start engine: {e}")


@router.post("/stop")
async def stop_engine(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Stop C engine process gracefully via Docker API
    
    Returns:
        Success status
    """
    import docker
    import os
    
    # Check if engine is running
    shm_path = "/dev/shm/draizer_v2"
    
    if not os.path.exists(shm_path):
        return {
            'success': True,
            'message': '⚠️ Engine was not running'
        }
    
    # Stop container via Docker API
    try:
        # Connect to Docker via Unix socket
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        
        # Get container
        container = client.containers.get('draizer_c_engine')
        
        # Stop container (timeout=10s for graceful shutdown)
        container.stop(timeout=10)
        
        # Disconnect bridge from old shared memory
        bridge = get_bridge()
        bridge.disconnect()
        
        return {
            'success': True,
            'message': '✅ C engine stopped successfully'
        }
            
    except docker.errors.NotFound:
        return {
            'success': True,
            'message': '⚠️ Engine container not found'
        }
    except docker.errors.APIError as e:
        raise HTTPException(status_code=503, detail=f"Docker API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to stop engine: {e}")


@router.post("/restart")
async def restart_engine(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Restart C engine
    
    Returns:
        Success status
    """
    bridge = get_bridge()
    
    success = bridge.restart_engine()
    
    if not success:
        raise HTTPException(status_code=503, detail="Failed to restart engine")
    
    return {
        'success': True,
        'message': 'Engine restarted successfully'
    }


@router.get("/config")
async def get_engine_config(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get current engine configuration
    
    Returns:
        Engine config dict
    """
    # Read from engine.json
    from pathlib import Path
    import json
    import os
    
    # Use absolute path in container
    config_path = Path("/app/c_engine/config/engine.json")
    
    if not config_path.exists():
        raise HTTPException(status_code=404, detail=f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return config


@router.post("/config")
async def save_engine_config(
    config: Dict,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Save engine configuration
    
    Args:
        config: New configuration dict
    
    Returns:
        Success status
    """
    from pathlib import Path
    import json
    
    # Use absolute path in container
    config_path = Path("/app/c_engine/config/engine.json")
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return {
            'success': True,
            'message': 'Configuration saved. Restart engine to apply changes.'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")


@router.post("/shutdown")
async def shutdown_engine(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Gracefully shutdown C engine
    
    ⚠️  Use with caution!
    """
    bridge = get_bridge()
    
    success = bridge.stop_engine()
    
    if not success:
        raise HTTPException(status_code=503, detail="Failed to shutdown engine")
    
    return {
        'success': True,
        'message': 'Engine shutdown initiated'
    }


@router.get("/health")
async def health_check() -> Dict:
    """
    Health check (no auth required)
    
    Returns:
        Engine health status
    """
    bridge = get_bridge()
    
    return bridge.health_check()


@router.websocket("/logs/stream")
async def stream_logs(websocket: WebSocket):
    """
    WebSocket endpoint for streaming C engine logs in real-time
    
    Streams logs from Docker container to frontend
    """
    await websocket.accept()
    
    try:
        import docker
        import subprocess
        
        # Check if container exists
        try:
            client = docker.DockerClient(base_url='unix://var/run/docker.sock')
            container = client.containers.get('draizer_c_engine')
            container_name = container.name
        except docker.errors.NotFound:
            await websocket.send_json({
                'timestamp': int(time.time() * 1000),
                'level': 'ERROR',
                'message': 'C engine container not found'
            })
            await websocket.close()
            return
        except Exception as e:
            await websocket.send_json({
                'timestamp': int(time.time() * 1000),
                'level': 'ERROR',
                'message': f'Docker connection error: {str(e)}'
            })
            await websocket.close()
            return
        
        # Send initial logs (last 20 lines)
        try:
            result = subprocess.run(
                ['docker', 'logs', '--tail', '20', container_name],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            for line in result.stdout.split('\n') + result.stderr.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Determine log level
                level = 'INFO'
                if 'ERROR' in line or '❌' in line:
                    level = 'ERROR'
                elif 'WARN' in line or '⚠️' in line:
                    level = 'WARNING'
                elif 'DEBUG' in line:
                    level = 'DEBUG'
                elif '✅' in line:
                    level = 'SUCCESS'
                
                    await websocket.send_json({
                        'id': f"{int(time.time() * 1000)}_{hash(line) % 10000}",
                        'timestamp': int(time.time() * 1000),
                        'level': level,
                        'message': line
                    })
                await asyncio.sleep(0.01)  # Small delay to prevent flooding
        except Exception as e:
            print(f"Error sending initial logs: {e}")
        
        # Start streaming new logs in background
        process = await asyncio.create_subprocess_exec(
            'docker', 'logs', '-f', '--tail', '0', container_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        async def read_stream(stream, ws):
            """Read from stream and send to WebSocket"""
            try:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    
                    line_text = line.decode('utf-8', errors='ignore').strip()
                    if not line_text:
                        continue
                    
                    # Determine log level
                    level = 'INFO'
                    if 'ERROR' in line_text or '❌' in line_text:
                        level = 'ERROR'
                    elif 'WARN' in line_text or '⚠️' in line_text:
                        level = 'WARNING'
                    elif 'DEBUG' in line_text:
                        level = 'DEBUG'
                    elif '✅' in line_text:
                        level = 'SUCCESS'
                    
                    await ws.send_json({
                        'id': f"{int(time.time() * 1000)}_{hash(line_text) % 10000}",
                        'timestamp': int(time.time() * 1000),
                        'level': level,
                        'message': line_text
                    })
            except Exception as e:
                print(f"Stream read error: {e}")
        
        # Create tasks for both stdout and stderr
        tasks = [
            asyncio.create_task(read_stream(process.stdout, websocket)),
            asyncio.create_task(read_stream(process.stderr, websocket))
        ]
        
        # Wait for disconnect or error
        try:
            while True:
                # Check if client is still connected
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                except:
                    break
        finally:
            # Cleanup
            for task in tasks:
                task.cancel()
            process.kill()
            await process.wait()
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                'timestamp': int(time.time() * 1000),
                'level': 'ERROR',
                'message': f'Streaming error: {str(e)}'
            })
        except:
            pass

