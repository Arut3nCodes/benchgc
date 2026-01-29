import argparse
import json
import subprocess
import time
import sys
import datanalysis as da
from pathlib import Path

def load_java_gc_profiles(profile_path):
    try:
        with open(profile_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"GC profile file {profile_path} not found. Using default profiles.")
        return {"serial": ["-XX:+UseSerialGC"]}
    
def load_java_app_profiles(profile_path):
    try:
        with open(profile_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "default": {
                "testPath": ".//tests/DemoApp.jar",
                "coresProfile": "single_core",
                "memoryProfile": "light",
                "pausesRequired": "short"
            }
        }

def run_jar(jar_path, app_profile, gc_name, gc_flags, duration, log_path=None):
    # Construct the Java command
    # -Xlog:gc focuses on GC metrics
    list_of_lines = []
    print(gc_flags)
    cmd = ["java"] + gc_flags
    
    if log_path:
        cmd.append(f"-Xlog:gc:file={log_path}")
    else:
        cmd.append("-Xlog:gc") # Output to stdout/stderr if no file

    cmd += ["-jar", jar_path]

    print(f"--- Starting: {' '.join(cmd)} ---")
    
    start_time = time.time()
    try:
        # Start the process
        proc = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True
        )

        # Monitor duration
        while True:
            # Check if process finished early
            if proc.poll() is not None:
                break
            
            line_dict = {}
            
            line_dict["gc_name"] = gc_name
            line_dict["gc_flags"] = gc_flags
            
            # Check if duration exceeded
            if duration and (time.time() - start_time) > duration:
                print(f"Time limit of {duration}s reached. Terminating...")
                proc.terminate()
                break
            
            # Print live output to terminal
            line = proc.stdout.readline()
            
            if line and line.startswith("["):
                transformed_line = da.transform_line(line.strip())
                line_dict.update(transformed_line if transformed_line else {})
                print(line_dict)
            else:
                print(line.strip())
        
    
    
            
    except KeyboardInterrupt:
        proc.kill()
        sys.exit("\nInterrupted by user.")

def run_cli():
    parser = argparse.ArgumentParser(description="BenchGC: Unified GC Benchmarking Tool for multiple programming language environments")
    subparsers = parser.add_subparsers(title="Language benchmarks", dest="language")
    
    jvm_parser = subparsers.add_parser("java", help="Run Java JVM GC benchmarks")
    jvm_parser.add_argument("test_profile", help="Select one of the predefined application profiles")
    jvm_parser.add_argument("--gc_profile", default="serial", help="GC profile name from json")
    jvm_parser.add_argument("--config", default="javaGcProfiles.json", help="Path to custom GC profiles JSON")
    jvm_parser.add_argument("--runs", type=int, default=1, help="Number of times to run")
    jvm_parser.add_argument("--app_profiles", default="javaAppProfiles.json", help="Path to custom application profiles JSON")
    jvm_parser.add_argument("--duration", type=int, default=30, help="Max duration per run (seconds)")
    jvm_parser.add_argument("--out", help="Path to save raw GC logs")
    
    go_parser = subparsers.add_parser("go", help="Run Go benchmarks")
    
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    
    if args.language == "java":
        gc_profiles = load_java_gc_profiles(args.config)
        app_profiles = load_java_app_profiles(args.app_profiles)
        gc_flags = gc_profiles.get(args.gc_profile, gc_profiles["serial"])
        test_profile = app_profiles.get(args.test_profile, app_profiles["default"])

        for i in range(args.runs):
            print(f"\n[Run {i+1}/{args.runs}] Profile: {args.gc_profile}")
            
            # If output path is provided, give each run a unique filename
            current_log = f"{args.out}_run{i}.log" if args.out else None
            
            run_jar(test_profile["testPath"], test_profile, args.gc_profile, gc_flags, args.duration, current_log)
    elif args.language == "go":
        print("Go benchmarking not yet implemented.")

if __name__ == "__main__":
    run_cli()