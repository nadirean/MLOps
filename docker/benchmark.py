import time
import requests
import statistics

def benchmark(url, num_requests=100):
    print(f"Benchmarking {url} with {num_requests} requests...")
    times = []
    payload = {"text": "This is a sample text for benchmarking the inference server."}

    # Warmup
    try:
        requests.post(f"{url}/predict", json=payload)
    except Exception as e:
        print(f"Error connecting to {url}: {e}")
        return

    for i in range(num_requests):
        try:
            start = time.time()
            response = requests.post(f"{url}/predict", json=payload)
            end = time.time()
            if response.status_code == 200:
                times.append((end - start) * 1000)
            else:
                print(f"Request {i} failed: {response.status_code}")
        except Exception as e:
            print(f"Request {i} error: {e}")

    if times:
        avg_time = statistics.mean(times)
        print(f"Average response time: {avg_time:.2f} ms")
        return avg_time
    else:
        print("No successful requests.")
        return None

if __name__ == "__main__":
    print("\nPyTorch Benchmark")
    benchmark("http://localhost:8000")
    
    print("\nONNX Benchmark")
    benchmark("http://localhost:8001")