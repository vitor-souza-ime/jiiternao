#!/usr/bin/env python3
"""
NAO Camera Jitter Benchmark - Concise Data Collection
====================================================
Focuses on essential data collection for posterior analysis.
"""

import qi
import cv2
import numpy as np
import time
import json
import os
import pandas as pd
from datetime import datetime

class NAOJitterBenchmark:
    def __init__(self, nao_ip="172.15.1.29", nao_port=9559):
        self.NAO_IP = nao_ip
        self.NAO_PORT = nao_port
        self.session = None
        self.video_service = None
        self.subscriber_id = None
        
        # Test configurations
        self.configs = [
            (2, 15, "VGA_15fps"),   # VGA, 15fps
            (2, 30, "VGA_30fps"),   # VGA, 30fps  
            (1, 15, "QVGA_15fps"),  # QVGA, 15fps
            (1, 30, "QVGA_30fps"),  # QVGA, 30fps
        ]
        
        # Results storage
        self.results = {}
        
    def connect(self):
        """Connect to NAO."""
        try:
            self.session = qi.Session()
            self.session.connect(f"tcp://{self.NAO_IP}:{self.NAO_PORT}")
            self.video_service = self.session.service("ALVideoDevice")
            print(f"✓ Connected to NAO")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def subscribe_camera(self, resolution_idx, fps):
        """Subscribe to camera."""
        try:
            if self.subscriber_id:
                self.video_service.unsubscribe(self.subscriber_id)
            
            self.subscriber_id = self.video_service.subscribeCamera(
                f"benchmark_{resolution_idx}_{fps}", 
                0, resolution_idx, 11, fps
            )
            return True
        except Exception as e:
            print(f"✗ Camera subscription failed: {e}")
            return False
    
    def measure_temporal_jitter(self, config_name, resolution_idx, fps, duration=30):
        """Measure temporal jitter - core test."""
        print(f"Testing {config_name}...")
        
        if not self.subscribe_camera(resolution_idx, fps):
            return None
            
        # Data collection
        timestamps = []
        intervals = []
        expected_interval = 1.0 / fps
        
        start_time = time.perf_counter()
        last_timestamp = None
        frame_count = 0
        errors = 0
        
        while time.perf_counter() - start_time < duration:
            try:
                capture_start = time.perf_counter()
                nao_image = self.video_service.getImageRemote(self.subscriber_id)
                capture_end = time.perf_counter()
                
                if nao_image is None:
                    errors += 1
                    continue
                
                timestamps.append(capture_end)
                frame_count += 1
                
                if last_timestamp is not None:
                    interval = capture_end - last_timestamp
                    intervals.append(interval)
                
                last_timestamp = capture_end
                
            except Exception:
                errors += 1
                continue
        
        if len(intervals) < 5:
            return None
        
        # Calculate metrics
        intervals_array = np.array(intervals)
        
        return {
            'config': config_name,
            'resolution_idx': resolution_idx,
            'target_fps': fps,
            'duration': duration,
            'frames_captured': frame_count,
            'errors': errors,
            'expected_interval': expected_interval,
            'intervals': intervals_array.tolist(),
            'timestamps': timestamps,
            # Core metrics
            'mean_interval': float(np.mean(intervals_array)),
            'std_interval': float(np.std(intervals_array)),
            'min_interval': float(np.min(intervals_array)),
            'max_interval': float(np.max(intervals_array)),
            'jitter_rms': float(np.sqrt(np.mean((intervals_array - expected_interval) ** 2))),
            'jitter_p2p': float(np.max(intervals_array) - np.min(intervals_array)),
            'cv_percent': float((np.std(intervals_array) / np.mean(intervals_array)) * 100),
            'actual_fps': float(1.0 / np.mean(intervals_array)),
            'efficiency_percent': float((1.0 / np.mean(intervals_array)) / fps * 100),
            'drop_rate_percent': float(errors / (frame_count + errors) * 100 if (frame_count + errors) > 0 else 0)
        }
    
    def measure_spatial_stability(self, config_name, resolution_idx, fps, duration=15):
        """Quick spatial stability test."""
        print(f"Spatial test {config_name}...")
        
        if not self.subscribe_camera(resolution_idx, fps):
            return None
            
        frames = []
        start_time = time.perf_counter()
        
        while time.perf_counter() - start_time < duration and len(frames) < 100:
            try:
                nao_image = self.video_service.getImageRemote(self.subscriber_id)
                if nao_image is None:
                    continue
                
                width, height = nao_image[0], nao_image[1]
                array = nao_image[6]
                frame = np.frombuffer(array, dtype=np.uint8).reshape((height, width, 3))
                frame_gray = cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), cv2.COLOR_BGR2GRAY)
                
                frames.append(frame_gray)
                
            except Exception:
                continue
        
        if len(frames) < 20:
            return None
        
        # Frame-to-frame differences
        frame_diffs = []
        for i in range(1, len(frames)):
            diff = cv2.absdiff(frames[i-1], frames[i])
            frame_diffs.append(np.mean(diff))
        
        frame_diffs_array = np.array(frame_diffs)
        
        return {
            'config': config_name,
            'frames_analyzed': len(frames),
            'mean_frame_diff': float(np.mean(frame_diffs_array)),
            'std_frame_diff': float(np.std(frame_diffs_array)),
            'max_frame_diff': float(np.max(frame_diffs_array)),
            'spatial_stability_metric': float(1.0 / (1.0 + np.mean(frame_diffs_array)))
        }
    
    def run_benchmark(self, output_dir="benchmark_data"):
        """Run complete benchmark."""
        print("="*50)
        print("NAO Camera Jitter Benchmark")
        print("="*50)
        
        if not self.connect():
            return False
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Run temporal tests
        temporal_results = []
        for resolution_idx, fps, config_name in self.configs:
            result = self.measure_temporal_jitter(config_name, resolution_idx, fps)
            if result:
                temporal_results.append(result)
                print(f"  {config_name}: {result['actual_fps']:.1f} fps actual, {result['jitter_rms']*1000:.1f}ms jitter")
        
        # Run spatial tests (VGA only)
        spatial_results = []
        for resolution_idx, fps, config_name in self.configs:
            if resolution_idx == 2:  # VGA only
                result = self.measure_spatial_stability(config_name, resolution_idx, fps)
                if result:
                    spatial_results.append(result)
                    print(f"  {config_name} spatial: {result['spatial_stability_metric']:.4f} stability")
        
        # Save raw data
        all_data = {
            'timestamp': timestamp,
            'temporal_jitter': temporal_results,
            'spatial_stability': spatial_results
        }
        
        # JSON for detailed analysis
        json_file = os.path.join(output_dir, f"nao_benchmark_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump(all_data, f, indent=2)
        
        # CSV for quick analysis
        if temporal_results:
            df_temporal = pd.DataFrame(temporal_results)
            csv_file = os.path.join(output_dir, f"temporal_data_{timestamp}.csv")
            df_temporal.to_csv(csv_file, index=False)
        
        if spatial_results:
            df_spatial = pd.DataFrame(spatial_results)
            csv_spatial = os.path.join(output_dir, f"spatial_data_{timestamp}.csv")
            df_spatial.to_csv(csv_spatial, index=False)
        
        # Quick summary
        summary_file = os.path.join(output_dir, f"summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write("NAO Camera Benchmark Summary\n")
            f.write("="*30 + "\n\n")
            
            f.write("TEMPORAL JITTER RESULTS:\n")
            for result in temporal_results:
                f.write(f"{result['config']}: {result['actual_fps']:.1f}fps ({result['efficiency_percent']:.1f}%), "
                       f"Jitter: {result['jitter_rms']*1000:.1f}ms RMS, CV: {result['cv_percent']:.1f}%\n")
            
            if spatial_results:
                f.write(f"\nSPATIAL STABILITY:\n")
                for result in spatial_results:
                    f.write(f"{result['config']}: Stability {result['spatial_stability_metric']:.4f}, "
                           f"Frame diff: {result['mean_frame_diff']:.2f}±{result['std_frame_diff']:.2f}\n")
        
        print(f"\n✓ Results saved to: {output_dir}")
        print(f"  - JSON data: {json_file}")
        print(f"  - CSV data: {csv_file}")
        print(f"  - Summary: {summary_file}")
        
        self.cleanup()
        return True
    
    def cleanup(self):
        """Clean up."""
        try:
            if self.subscriber_id and self.video_service:
                self.video_service.unsubscribe(self.subscriber_id)
        except:
            pass

def main():
    """Main execution."""
    nao_ip = input("NAO IP (default: 172.15.1.29): ").strip() or "172.15.1.29"
    
    benchmark = NAOJitterBenchmark(nao_ip)
    
    try:
        success = benchmark.run_benchmark()
        if success:
            print("\n✓ Benchmark completed!")
        else:
            print("\n✗ Benchmark failed!")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        benchmark.cleanup()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        benchmark.cleanup()

if __name__ == "__main__":
    main()
