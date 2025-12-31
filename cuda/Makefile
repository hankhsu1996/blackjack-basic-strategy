# CUDA Monte Carlo Makefile

NVCC = /usr/local/cuda/bin/nvcc
NVCC_FLAGS = -O3

# RTX 3080 = sm_86, RTX 3070 = sm_86, RTX 2080 = sm_75
ARCH = -arch=sm_86

TARGET = monte_carlo
SRC = monte_carlo.cu cJSON.c
STRATEGY = ../web/public/strategies/6-h17-das-rsa-peek-32.json

.PHONY: all clean run test precision

all: $(TARGET)

$(TARGET): monte_carlo.cu cJSON.c cJSON.h
	$(NVCC) $(NVCC_FLAGS) $(ARCH) -o $@ monte_carlo.cu cJSON.c

clean:
	rm -f $(TARGET)

# Quick test: 1 billion hands
test: $(TARGET)
	./$(TARGET) $(STRATEGY) 1

# Standard run: 10 billion hands
run: $(TARGET)
	./$(TARGET) $(STRATEGY) 10

# High precision: 40 billion hands (~±0.001% accuracy)
precision: $(TARGET)
	./$(TARGET) $(STRATEGY) 40
