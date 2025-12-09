# DRAIZER V2.0 - Makefile (alternative to CMake)

CC = gcc
CFLAGS = -O3 -march=native -mtune=native -flto -ffast-math -funroll-loops -mavx2 -mfma -DNDEBUG -Wall -Wextra
LDFLAGS = -flto -Wl,-O3
LIBS = -luring -lcurl -lyyjson -lssl -lcrypto -lpthread -lm

# Directories
SRC_DIR = src
BUILD_DIR = build
BIN_DIR = $(BUILD_DIR)/bin
OBJ_DIR = $(BUILD_DIR)/obj

# Source files (placeholder for now)
SOURCES = $(SRC_DIR)/main.c

# Object files
OBJECTS = $(SOURCES:$(SRC_DIR)/%.c=$(OBJ_DIR)/%.o)

# Executable
TARGET = $(BIN_DIR)/draizer_engine

# Default target
all: $(TARGET)

# Create directories
$(BUILD_DIR) $(BIN_DIR) $(OBJ_DIR):
	mkdir -p $@

# Compile
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Link
$(TARGET): $(OBJECTS) | $(BIN_DIR)
	$(CC) $(LDFLAGS) $(OBJECTS) $(LIBS) -o $@
	@echo "✓ Built: $@"

# Run
run: $(TARGET)
	$(TARGET) --mode paper --capital 1000

# Clean
clean:
	rm -rf $(BUILD_DIR)

# Debug build
debug: CFLAGS = -O0 -g -fsanitize=address -fsanitize=undefined -DDEBUG -Wall -Wextra
debug: $(TARGET)

# Install
install: $(TARGET)
	install -D $(TARGET) /usr/local/bin/draizer_engine
	install -D config/engine.json /etc/draizer/engine.json
	install -D config/strategies.json /etc/draizer/strategies.json

.PHONY: all run clean debug install


