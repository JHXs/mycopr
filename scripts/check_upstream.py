import argparse
import json
import sys
from common import fetch_upstream_data, is_update_needed, load_packages

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force updates for all packages")
    args = parser.parse_args()

    packages = load_packages()

    to_update = []
    for name, cfg in packages.items():
        try:
            data = fetch_upstream_data(cfg)
            if args.force or is_update_needed(cfg, data):
                to_update.append({"name": name, "data": data})
        except Exception as e:
            print(f"Error fetching {name}: {e}", file=sys.stderr)

    print(json.dumps(to_update))

if __name__ == "__main__":
    main()
