# CUDA Monte Carlo Blackjack Simulator

High-performance GPU-accelerated Monte Carlo simulation for calculating blackjack house edge.

## Features

- Loads strategy and rules from JSON file
- Finite deck simulation with proper shoe and reshuffling
- ~290 million hands/second on RTX 3080

## Prerequisites (WSL2 Ubuntu)

### 1. Windows NVIDIA Driver

Your Windows NVIDIA driver must be version 470.76+ (you likely already have this with an RTX 3080).

Check in Windows:

```
nvidia-smi
```

### 2. Install CUDA Toolkit in WSL

```bash
# Add NVIDIA package repository
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update

# Install CUDA toolkit (compiler and libraries)
sudo apt-get install -y cuda-toolkit-12-4

# Add to PATH (add to ~/.bashrc for persistence)
export PATH=/usr/local/cuda/bin:$PATH
```

### 3. Verify Installation

```bash
nvcc --version
nvidia-smi
```

## Building

```bash
cd cuda
make
```

## Usage

```bash
# Quick test: 1 billion hands (~±0.005% precision)
make test

# Standard run: 10 billion hands (~±0.002% precision)
make run

# High precision: 40 billion hands (~±0.001% precision)
make precision
```

Or run directly with a strategy file:

```bash
./monte_carlo ../web/public/strategies/6-h17-das-rsa-peek-32.json 10
```

## Expected Output

```
Loading strategy from: ../web/public/strategies/6-h17-das-rsa-peek-32.json
Config: Decks=6, H17=Yes, Peek=Yes, BJ=1.50

=== CUDA Monte Carlo Blackjack Simulator ===
Target: 10 billion hands
Threads: 8704

Running simulation...

=== Results ===
Hands: 10.00 billion
House edge: 0.6971% +/- 0.0022%
95% CI: [0.6949%, 0.6994%]
Time: 34.69 seconds
Speed: 288.28 million hands/sec
```

## Precision vs Hands

Standard error scales as 1/√n:

| Hands | Standard Error | 95% CI  | Time (RTX 3080) |
| ----- | -------------- | ------- | --------------- |
| 1B    | ±0.006%        | ±0.012% | ~4s             |
| 10B   | ±0.002%        | ±0.004% | ~35s            |
| 40B   | ±0.001%        | ±0.002% | ~140s           |

## Troubleshooting

### "CUDA driver version is insufficient"

Update your Windows NVIDIA driver to the latest version.

### "no CUDA-capable device is detected"

1. Make sure you're on WSL2 (not WSL1): `wsl --status`
2. Update WSL: `wsl --update`
3. Restart WSL: `wsl --shutdown` then reopen

## Technical Details

- Each CUDA thread maintains its own shoe
- Fisher-Yates shuffle for true random shoe
- Reshuffles at 75% penetration
- One split allowed, split aces get one card only
- Dealer peeks for blackjack (configurable via JSON)
