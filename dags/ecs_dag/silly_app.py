import os
import subprocess
import time

import numpy as np  # test requirements.txt was installed

# AWS_REGION = os.environ["AWS_REGION"]



if __name__ == "__main__":
    print("env vars", os.environ)
    for i in range(60):
        print(i)
        time.sleep(1)

    proc = subprocess.run(["pip3", "list"], capture_output=True)
    print(proc.stdout.decode("utf-8"))