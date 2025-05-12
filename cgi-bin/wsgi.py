#!/usr/bin/env python3


from controller import app
import sys
import uvicorn


sys.path.append("../lib/")

if __name__ == "__main__":
   uvicorn.run("controller:app", host="0.0.0.0", port=19000)
