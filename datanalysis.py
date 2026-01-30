from datetime import datetime
import re

# We define the regex outside the function so it's compiled once for speed
GC_PATTERN = re.compile(
    r"\[(?P<timestamp>[\d\.]+)s\].*?"                # [0.123s]
    r"GC\(\d+\) (?P<type>.*?) "                      # GC(0) Pause Young...
    r"(?P<mem_before>[\d\.]+)(?P<u1>[KMG])->"        # 24M->
    r"(?P<mem_after>[\d\.]+)(?P<u2>[KMG])"           # 10M
    r"\((?P<mem_total>[\d\.]+)(?P<u3>[KMG])\) "      # (256M)
    r"(?P<duration>[\d\.]+)ms"                       # 5.123ms
)

def to_mb(value, unit):
    """Helper to keep units consistent."""
    multiplier = {'K': 1/1024, 'M': 1, 'G': 1024}
    return round(float(value) * multiplier.get(unit, 1), 2)

def transform_line(raw_line):
    """
    Parses a single raw GC log line into a uniform dictionary.
    Returns None if the line is not a GC event.
    """
    match = GC_PATTERN.search(raw_line)
    if not match:
        return None
    
    data = match.groupdict()
    
    # Return the "Uniform" style dictionary
    return {
        "ts": float(data['timestamp']),
        "event": data['type'].strip(),
        "before_mb": to_mb(data['mem_before'], data['u1']),
        "after_mb": to_mb(data['mem_after'], data['u2']),
        "total_mb": to_mb(data['mem_total'], data['u3']),
        "pause_ms": float(data['duration'])
    }

def save_results_to_csv(language, results, output_path = "results"):
    """Saves a list of result dictionaries to a CSV file."""
    import csv

    if not results:
        print("No results to save.")
        return

    # Get all unique keys for the header
    
    fieldnames = []
    currTime = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_name = language + "_" + results[0]["profile_name"] + "_" + results[0]["gc_name"] + "_" + currTime + "_results.csv"
    output_path = output_path + "/" + file_name
 
    for result in results:
        for key in result.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

    print(f"Results saved to {output_path}")

GO_GC_REGEX = re.compile(
    r"gc\s+(?P<cycle>\d+)\s+@(?P<time>[0-9.]+)s\s+(?P<cpu>\d+)%:"
    r"\s+(?P<stw1>[0-9.]+)\+(?P<mark>[0-9.]+)\+(?P<stw2>[0-9.]+)\s+ms clock,"
    r"\s+(?P<cpu1>[0-9.]+)\+(?P<cpu2>[0-9.]+)/(?P<cpu3>[0-9.]+)/(?P<cpu4>[0-9.]+)\+(?P<cpu5>[0-9.]+)\s+ms cpu,"
    r"\s+(?P<heap_before>\d+)->(?P<heap_after>\d+)->(?P<heap_live>\d+)\s+MB,"
    r"\s+(?P<goal>\d+)\s+MB goal,.*?(?P<p>\d+)\s+P"
)

def transform_go_line(line):
    m = GO_GC_REGEX.search(line)
    if not m:
        return None

    return {
        "cycle": int(m["cycle"]),
        "time_s": float(m["time"]),
        "cpu_percent": int(m["cpu"]),
        "stw_start_ms": float(m["stw1"]),
        "mark_ms": float(m["mark"]),
        "stw_end_ms": float(m["stw2"]),
        "heap_before_mb": int(m["heap_before"]),
        "heap_after_mb": int(m["heap_after"]),
        "heap_live_mb": int(m["heap_live"]),
        "heap_goal_mb": int(m["goal"]),
        "procs": int(m["p"]),
    }

