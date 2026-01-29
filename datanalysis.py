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