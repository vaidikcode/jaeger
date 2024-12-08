import subprocess
import argparse
from datetime import datetime

def scrape_metrics(url, output_file):
    """
    Scrape metrics from the given URL and save them to a file.
    """
    try:
        command = f"prom2json {url}"
        print(f"Scraping metrics from {url}...")
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, text=True)
        with open(output_file, "w") as f:
            f.write(result.stdout)
        print(f"Metrics saved to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error scraping metrics from {url}: {e.stderr}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Scrape metrics from Jaeger instances.")
    parser.add_argument("--version", required=True, choices=["v1", "v2"], help="Jaeger version (v1 or v2).")
    parser.add_argument("--output", required=True, help="Output file to save metrics.")
    args = parser.parse_args()

    # Determine the Jaeger metrics endpoint
    if args.version == "v1":
        jaeger_url = "http://localhost:14269/metrics"
    elif args.version == "v2":
        jaeger_url = "http://localhost:8888/metrics"
    else:
        raise ValueError("Invalid version. Use 'v1' or 'v2'.")

    # Scrape metrics
    scrape_metrics(jaeger_url, args.output)

if __name__ == "__main__":
    main()

