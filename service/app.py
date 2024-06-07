import os
import time

# AWS_REGION = os.environ["AWS_REGION"]



if __name__ == "__main__":
    print("env vars", os.environ)
    for i in range(60):
        print(i)
        time.sleep(1)
        # return {"hi": "thanks"}
