from ttdiagnosis.run_diagnosis import run_diagnosis
import time
import signal
import sys

PERIOD = 1200 # 20 min
running = False

def signal_handler(signal, frame):
    global running
    print("Int signal received")
    running = False

def run():
    try:
        run_diagnosis(silent=False)
    except Exception as e:
        print("ERROR executing diagnosis:", e)

def start():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    running = True

    # Wait 60s for heimdall init
    next_time = time.monotonic() + 60
    while running:
        curr_time = time.monotonic()
        if curr_time >= next_time:
            while next_time <= curr_time:
                next_time = next_time + PERIOD
            print("Executing diagnosis")
            try:
                run_diagnosis(silent=True)
            except Exception as e:
                print("ERROR executing diagnosis:", e)
        time.sleep(2)


    sys.exit(0)

