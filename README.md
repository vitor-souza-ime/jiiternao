# NAO Camera Jitter Benchmark

This project provides a benchmark tool to measure the **temporal jitter** and **spatial stability** of the NAO humanoid robot's camera. The script collects performance metrics at different resolutions and frame rates, producing detailed reports for further analysis.

---

## Features

- **Temporal jitter measurement**  
  Evaluates frame timing consistency using high-resolution timers (`time.perf_counter`), reporting metrics such as mean interval, RMS jitter, efficiency, and frame drop rate.

- **Spatial stability measurement**  
  Analyzes frame-to-frame differences in grayscale space to estimate spatial consistency of the video feed.

- **Multiple configurations**  
  Tests at VGA and QVGA resolutions with 15 and 30 fps.

- **Data export**  
  Results are saved in:
  - **JSON**: complete raw data  
  - **CSV**: structured temporal and spatial metrics  
  - **TXT**: quick summary report  

---

## Requirements

- Python 3.8+  
- NAOqi Python SDK  
- Dependencies:
  ```bash
  pip install opencv-python numpy pandas
````

---

## Usage

1. Clone the repository:

   ```bash
   git clone https://github.com/vitor-souza-ime/jitternao.git
   cd jitternao
   ```

2. Run the benchmark:

   ```bash
   python3 main.py
   ```

3. Enter your NAO robot’s IP address when prompted (default: `172.15.1.29`).

---

## Output

The benchmark creates a folder `benchmark_data/` with the following files:

* `nao_benchmark_<timestamp>.json` → full raw dataset
* `temporal_data_<timestamp>.csv` → temporal jitter metrics
* `spatial_data_<timestamp>.csv` → spatial stability metrics
* `summary_<timestamp>.txt` → concise human-readable report

Example console output:

```
==================================================
NAO Camera Jitter Benchmark
==================================================
✓ Connected to NAO
  VGA_15fps: 14.8 fps actual, 2.3ms jitter
  VGA_30fps: 28.5 fps actual, 3.1ms jitter
  QVGA_15fps: 15.0 fps actual, 1.7ms jitter
  QVGA_30fps: 29.8 fps actual, 2.0ms jitter
  VGA_15fps spatial: 0.9765 stability
  VGA_30fps spatial: 0.9823 stability

✓ Results saved to: benchmark_data
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

```

