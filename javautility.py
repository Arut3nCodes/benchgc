import json
import subprocess
import time
import datanalysis as da
import sys

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
            line_dict["profile_name"] = app_profile.get("profileName", "default")
            line_dict["cores_profile"] = app_profile.get("coresProfile", "unknown")
            line_dict["memory_profile"] = app_profile.get("memoryProfile", "unknown")
            line_dict["pauses_required"] = app_profile.get("pausesRequired", "unknown")
            
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
                list_of_lines.append(line_dict)
            else:
                print(line.strip())
        print(list_of_lines)
        list_of_lines = list_of_lines[1:]  # Remove the first entry which may be incomplete
        da.save_results_to_csv("java", list_of_lines)
        
    except KeyboardInterrupt:
        proc.kill()
        sys.exit("\nInterrupted by user.")
