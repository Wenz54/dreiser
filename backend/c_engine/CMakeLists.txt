cmake_minimum_required(VERSION 3.10)
project(draizer_v2 C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Optimization flags
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra -O3 -march=native")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -mavx2 -mfma")  # SIMD
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -pthread")

# Ultra-performance flags (from DRAIZER_V2_FINAL_COMPACT.md)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -flto")                    # Link-time optimization
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fomit-frame-pointer")     # Remove frame pointer
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -ffast-math")              # Fast math
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -funroll-loops")           # Unroll loops
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -falign-functions=64")     # 64-byte function alignment
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fprofile-generate")       # Step 1 of PGO

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/src)

# Source files
set(SOURCES
    src/main.c
    src/utils/timestamp.c
    src/utils/memory_pool.c
    src/data/spsc_ring.c
    src/data/price_cache.c
    # NEW: Spot-Futures arbitrage strategy (Bitfinex <-> Deribit)
    src/strategies/spot_futures_arbitrage.c
    src/strategies/statistical_arbitrage.c
    src/strategies/triangular.c
    # Legacy risk manager + new HFT risk manager
    src/risk/risk_manager.c
    src/risk/hft_risk_manager.c
    src/execution/virtual_portfolio.c
    src/ipc/shared_memory.c
    # Network layer
    src/network/websocket.c
    src/network/exchange.c
    # NEW: Bitfinex (spot) + Deribit (futures perpetual)
    src/network/bitfinex_ws.c
    src/network/deribit_ws.c
)

# Executable
add_executable(draizer_engine ${SOURCES})

# Find OpenSSL
find_package(OpenSSL REQUIRED)
include_directories(${OPENSSL_INCLUDE_DIR})

# Link libraries
target_link_libraries(draizer_engine
    pthread
    m           # Math library
    rt          # Real-time extensions (for shm_open)
    ${OPENSSL_LIBRARIES}  # OpenSSL for WSS support
    yyjson      # JSON parsing
)

# Install target
install(TARGETS draizer_engine DESTINATION bin)

# Print configuration
message(STATUS "========================================")
message(STATUS "DRAIZER V2.0 C ENGINE BUILD CONFIGURATION")
message(STATUS "========================================")
message(STATUS "Compiler: ${CMAKE_C_COMPILER}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C Flags: ${CMAKE_C_FLAGS}")
message(STATUS "Target: draizer_engine")
message(STATUS "========================================")
