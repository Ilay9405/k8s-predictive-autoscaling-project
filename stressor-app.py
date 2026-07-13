import time
import math
import requests
import threading

TARGET_URL = "http://localhost:8080"
BASE_TRAFFIC = 2   # Minimum requests per second
PEAK_TRAFFIC = 40  # Maximum requests per second at the peak of the spike
CYCLE_MINUTES = 10 # Traffic spikes every 10 minutes

def make_request():
    try:
        requests.get(TARGET_URL, timeout=2)
    except:
        pass

print("Starting Predictive Load Generator...")
print(f"Target: {TARGET_URL} | Cycle: {CYCLE_MINUTES} mins")

while True:
    # Calculate a smooth sine wave based on the current time (0.0 to 1.0)
    current_time = time.time()
    cycle_position = (current_time % (CYCLE_MINUTES * 60)) / (CYCLE_MINUTES * 60)
    sine_wave = (math.sin(cycle_position * 2 * math.pi - (math.pi / 2)) + 1) / 2
    
    # Calculate exact Requests Per Second (RPS) for this exact moment
    current_rps = int(BASE_TRAFFIC + (sine_wave * (PEAK_TRAFFIC - BASE_TRAFFIC)))
    print(f"[{time.strftime('%H:%M:%S')}] Pumping Load: {current_rps} RPS")
    
    # Fire off the requests simultaneously
    threads = []
    for _ in range(current_rps):
        t = threading.Thread(target=make_request)
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()
        
    # Wait until the next second
    time.sleep(1)
