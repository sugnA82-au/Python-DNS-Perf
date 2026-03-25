#!/usr/bin/env python3
import argparse
import subprocess
import re
import sys
import os
import random
import string
import time
import tempfile

DEFAULT_DOMAINS = [
    "google.com", "amazon.com", "apple.com", "facebook.com", "microsoft.com",
    "netflix.com", "github.com", "cloudflare.com", "wikipedia.org", "youtube.com"
]

def generate_random_subdomain(domain):
    prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{prefix}.{domain}"

def generate_query_file(file_path, count=10000, cache_bust=False):
    print(f"[*] Generating query file ({'Cache-Bust ON' if cache_bust else 'Cache-Bust OFF'}) at {file_path}...")
    with open(file_path, "w") as f:
        for i in range(count):
            domain = DEFAULT_DOMAINS[i % len(DEFAULT_DOMAINS)]
            if cache_bust:
                domain = generate_random_subdomain(domain)
            f.write(f"{domain} A\n")

def run_dnsperf(target, query_file, rate, duration=10):
    cmd = ["dnsperf", "-s", target, "-d", query_file, "-Q", str(rate), "-l", str(duration)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout + result.stderr
        
        actual_qps_match = re.search(r"Queries per second:\s+([\d.]+)", output)
        loss_match = re.search(r"Queries lost:\s+\d+\s+\(([\d.]+)%\)", output)
        
        # fallback latency measurement using dig if dnsperf reports 0
        latency_match = re.search(r"Average latency:\s+([1-9][\d.]+)", output)
        if not latency_match:
            # Quick dig sample to get real network latency
            dig_res = subprocess.run(["dig", f"@{target}", "google.com"], capture_output=True, text=True)
            dig_latency = re.search(r"Query time: (\d+) msec", dig_res.stdout)
            latency = float(dig_latency.group(1)) if dig_latency else 0.0
        else:
            latency = float(latency_match.group(1)) * 1000
        
        actual_qps = actual_qps_match.group(1) if actual_qps_match else "0.0"
        loss = loss_match.group(1) if loss_match else "0.0"
        
        return actual_qps, loss, latency
    except FileNotFoundError:
        print("[!] Error: 'dnsperf' not found in PATH.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="DNS Stepping Benchmark Tool (with Cache-Busting)")
    parser.add_argument("target", help="DNS server IP address")
    parser.add_argument("-q", "--query-file", help="Path to query file")
    parser.add_argument("-m", "--max-rate", type=int, default=500, help="Max QPS")
    parser.add_argument("-s", "--step", type=int, default=100, help="Step size")
    parser.add_argument("-d", "--duration", type=int, default=10, help="Duration per step")
    parser.add_argument("--cache-bust", action="store_true", help="Force unique queries to bypass cache")

    args = parser.parse_args()

    query_file = args.query_file or os.path.join(tempfile.gettempdir(), "dns_bench_queries.txt")
    generate_query_file(query_file, count=args.max_rate * args.duration * 2, cache_bust=args.cache_bust)

    rates = range(args.step, args.max_rate + 1, args.step)
    
    print(f"\n[*] Starting benchmark for {args.target}")
    print(f"{'Target (qps)':<15} {'Actual (qps)':<15} {'Loss (%)':<10} {'Latency (ms)':<15}")
    print("-" * 55)
    
    for rate in rates:
        actual, loss, latency = run_dnsperf(args.target, query_file, rate, args.duration)
        print(f"{rate:<15} {actual:<15} {loss:<10} {latency:<15.1f}")
        
        if float(loss) >= 100.0:
            print(f"\n[!] Target {args.target} is not responding (100% loss). Stopping benchmark.")
            break

if __name__ == "__main__":
    main()
