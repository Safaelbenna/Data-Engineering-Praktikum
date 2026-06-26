import subprocess
import os
import time

BASE = os.path.dirname(__file__)

def main():
    start = time.perf_counter()
    subprocess.run(["py", os.path.join(BASE, "pipeline", "cli_ui.py")])
    subprocess.run(["py", os.path.join(BASE, "tool", "cli_ui.py")])
    seconds = time.perf_counter() - start
    print(f"\nTotal runtime (pipeline + tool): {seconds:.2f} seconds ({seconds/60:.2f} min)")

if __name__ == "__main__":
    main()


