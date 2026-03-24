# DNS Stepping Benchmark Tool

A lightweight Python tool for stress-testing DNS servers with a "stepping" pattern. It automates the process of ramping up query volume to identify performance bottlenecks and rate limits.

## Features

- **Stepping Benchmark**: Incrementally increase Queries Per Second (QPS) to find the breaking point of a DNS resolver.
- **Cache-Busting**: Optional mode to generate unique subdomains, forcing the resolver to perform full recursive lookups instead of serving from cache.
- **Early Exit**: Automatically stops the benchmark if a server becomes unresponsive (100% packet loss).
- **Latency Verification**: Combines `dnsperf` metrics with a fallback `dig` check to ensure accurate latency reporting.
- **Portable**: Automatically generates query files in the system's temporary directory.

## Prerequisites

- **Python 3.x**
- **dnsperf**: The underlying engine used for high-volume testing.
  - macOS: `brew install dnsperf`
  - Linux: `sudo apt-get install dnsperf` (or build from source)

## Installation

1. Clone this repository.
2. Make the script executable:
   ```bash
   chmod +x dns_bench.py
   ```

## Usage

Basic usage requires only the target DNS server IP:

```bash
./dns_bench.py <server_ip>
```

### Advanced Options

| Option | Description | Default |
|--------|-------------|---------|
| `-m, --max-rate` | Maximum QPS to reach | 500 |
| `-s, --step` | QPS increment per step | 100 |
| `-d, --duration` | Seconds to run each step | 10 |
| `--cache-bust` | Bypass cache with unique queries | Off |

### Examples

**Test local router performance:**
```bash
./dns_bench.py 192.168.1.1 -m 400 -s 50
```

**Benchmark a public resolver's recursive performance:**
```bash
./dns_bench.py 1.1.1.1 --cache-bust -m 1000 -s 200
```

## How it Works

The tool wraps the `dnsperf` utility, managing the generation of input query files and parsing the output into a clean tabular format. By using the `--cache-bust` flag, the tool ensures that every query is unique (e.g., `random_id.google.com`), providing a true measure of the resolver's backend lookup speed rather than its cache retrieval speed.

## License

MIT
