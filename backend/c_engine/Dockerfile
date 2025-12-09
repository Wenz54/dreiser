# DRAIZER V2 - C Engine Dockerfile
FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libssl-dev \
    pkg-config \
    wget \
    procps \
    libwebsockets-dev \
    && rm -rf /var/lib/apt/lists/*

# Install yyjson (fast JSON parser)
WORKDIR /tmp
RUN wget https://github.com/ibireme/yyjson/archive/refs/tags/0.8.0.tar.gz && \
    tar -xzf 0.8.0.tar.gz && \
    cd yyjson-0.8.0 && \
    mkdir build && cd build && \
    cmake .. && make && make install && \
    ldconfig && \
    cd /tmp && rm -rf yyjson-0.8.0 0.8.0.tar.gz

# Create app directory
WORKDIR /app/c_engine

# Copy C engine source
COPY . .

# Build C engine
RUN mkdir -p build && cd build && \
    cmake .. && \
    make -j$(nproc) && \
    echo "✅ C engine compiled successfully"

# Create log directory
RUN mkdir -p /var/log

# Expose shared memory volume
VOLUME ["/dev/shm"]

# Set working directory
WORKDIR /app/c_engine/build

# Health check script
RUN echo '#!/bin/bash\npgrep -f draizer_engine > /dev/null && exit 0 || exit 1' > /usr/local/bin/healthcheck.sh && \
    chmod +x /usr/local/bin/healthcheck.sh

# Run engine directly (graceful shutdown handled by engine itself)
CMD ["./draizer_engine"]

