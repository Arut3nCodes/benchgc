import subprocess
import time
import os
import sys
import datanalysis as da
import json

def load_go_gc_profiles(profile_path):
    try:
        with open(profile_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"default": ["GODEBUG=gctrace=1"]}

def load_go_app_profiles(profile_path):
    try:
        with open(profile_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "default": {
                "profileName": "default",
                "testPath": "./tests/demoapp",
                "coresProfile": "single_core",
                "memoryProfile": "light",
                "pausesRequired": "short"
            }
        }

def apply_go_env(gc_flags):
    env = os.environ.copy()
    for flag in gc_flags:
        if "=" in flag:
            k, v = flag.split("=", 1)
            env[k] = v
    return env

def run_go(binary_path, app_profile, gc_name, gc_flags, duration, log_path=None):
    list_of_lines = []

    env = apply_go_env(gc_flags)
    cmd = [binary_path]

    print(f"--- Starting Go: {' '.join(cmd)} ---")

    start_time = time.time()

    if log_path:
        log_file = open(log_path, "w")
    else:
        log_file = None

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env
        )

        while True:
            if proc.poll() is not None:
                break

            if duration and (time.time() - start_time) > duration:
                print(f"Time limit of {duration}s reached. Terminating...")
                proc.terminate()
                break

            line = proc.stdout.readline()

            if log_file:
                log_file.write(line)

            line_dict = {
                "gc_name": gc_name,
                "gc_flags": gc_flags,
                "profile_name": app_profile.get("profileName", "default"),
                "cores_profile": app_profile.get("coresProfile", "unknown"),
                "memory_profile": app_profile.get("memoryProfile", "unknown"),
                "pauses_required": app_profile.get("pausesRequired", "unknown"),
            }

            if line.startswith("gc"):
                transformed = da.transform_go_line(line.strip())
                if transformed:
                    line_dict.update(transformed)
                    print(line_dict)
                    list_of_lines.append(line_dict)
            else:
                print(line.strip())

        if list_of_lines:
            list_of_lines = list_of_lines[1:]
            da.save_results_to_csv("go", list_of_lines)

    except KeyboardInterrupt:
        proc.kill()
        sys.exit("\nInterrupted by user.")
    finally:
        if log_file:
            log_file.close()
