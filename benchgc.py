import argparse
import sys
import datanalysis as da
from pathlib import Path
import javautility as jutil
import goutility as gutil

def run_cli():
    parser = argparse.ArgumentParser(description="BenchGC: Unified GC Benchmarking Tool for multiple programming language environments")
    subparsers = parser.add_subparsers(title="Language benchmarks", dest="language")
    
    # Java JVM parser
    
    jvm_parser = subparsers.add_parser("java", help="Run Java JVM GC benchmarks")
    jvm_parser.add_argument("test_profile", help="Select one of the predefined application profiles")
    jvm_parser.add_argument("--gc_profile", default="serial", help="GC profile name from json")
    jvm_parser.add_argument("--config", default="javaGcProfiles.json", help="Path to custom GC profiles JSON")
    jvm_parser.add_argument("--runs", type=int, default=1, help="Number of times to run")
    jvm_parser.add_argument("--app_profiles", default="javaAppProfiles.json", help="Path to custom application profiles JSON")
    jvm_parser.add_argument("--duration", type=int, default=30, help="Max duration per run (seconds)")
    jvm_parser.add_argument("--out", help="Path to save raw GC logs")
    
    # Go parser
    
    go_parser = subparsers.add_parser("go", help="Run Go benchmarks")
    go_parser.add_argument("test_profile", help="Select one of the predefined application profiles")
    go_parser.add_argument("--gc_profile", default="default", help="GC profile name from json")
    go_parser.add_argument("--config", default="goGcProfiles.json", help="Path to custom GC profiles JSON")
    go_parser.add_argument("--runs", type=int, default=1, help="Number of times to run")
    go_parser.add_argument("--app_profiles", default="goAppProfiles.json", help="Path to custom application profiles JSON")
    go_parser.add_argument("--duration", type=int, default=30, help="Max duration per run (seconds)")
    go_parser.add_argument("--out", help="Path to save raw GC logs")
    
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    
    if args.language == "java":
        gc_profiles = jutil.load_java_gc_profiles(args.config)
        app_profiles = jutil.load_java_app_profiles(args.app_profiles)
        gc_flags = gc_profiles.get(args.gc_profile, gc_profiles["serial"])
        test_profile = app_profiles.get(args.test_profile, app_profiles["default"])
        print(test_profile)
        for i in range(args.runs):
            print(f"\n[Run {i+1}/{args.runs}] Profile: {args.gc_profile}")
            
            # If output path is provided, give each run a unique filename
            current_log = f"{args.out}_run{i}.log" if args.out else None
            
            jutil.run_jar(test_profile["testPath"], test_profile, args.gc_profile, gc_flags, args.duration, current_log)
    elif args.language == "go":
        gc_profiles = gutil.load_go_gc_profiles(args.config)
        app_profiles = gutil.load_go_app_profiles(args.app_profiles)

        gc_flags = gc_profiles.get(args.gc_profile, gc_profiles["default"])
        test_profile = app_profiles.get(args.test_profile, app_profiles["default"])

        for i in range(args.runs):
            print(f"\n[Run {i+1}/{args.runs}] Profile: {args.gc_profile}")

            current_log = f"{args.out}_run{i}.log" if args.out else None

            gutil.run_go(
                test_profile["testPath"],
                test_profile,
                args.gc_profile,
                gc_flags,
                args.duration,
                current_log
            )


if __name__ == "__main__":
    run_cli()