#!/usr/bin/env python3

import argparse
import subprocess
import sys

def run(cmd):
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--deploy_large_job', action='store_true')
    parser.add_argument('--deploy_small_job', action='store_true')
    parser.add_argument('--deploy_critical_job', action='store_true')

    parser.add_argument('--image', required=True)
    parser.add_argument('--container-name', required=True)

    args = parser.parse_args()

    # detect deploy type
    if args.deploy_large_job:
        deploy_type = "large"
    elif args.deploy_small_job:
        deploy_type = "small"
    elif args.deploy_critical_job:
        deploy_type = "critical"
    else:
        print("No deploy type given")
        sys.exit(1)

    print(f"Deploy type: {deploy_type}")
    print(f"Image: {args.image}")
    print(f"Container: {args.container_name}")

    # stop old container (if exists)
    run(["docker", "rm", "-f", args.container_name])

    # run container
    run([
        "docker", "run", "-d",
        "--name", args.container_name,
        "-p", "8080:80",
        args.image
    ])

    print("Container started successfully")

if __name__ == "__main__":
    main()
