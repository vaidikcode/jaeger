import os
import json
import argparse
import subprocess

def extract_metrics_with_labels(metrics, strip_prefix=None):
    result = {}
    for metric in metrics:
        name = metric['name']
        if strip_prefix and name.startswith(strip_prefix):
            name = name[len(strip_prefix):]
        labels = {}
        if 'metrics' in metric and 'labels' in metric['metrics'][0]:
            labels = metric['metrics'][0]['labels']
        result[name] = labels
    return result

def remove_overlapping_metrics(all_in_one_data, other_json_data):
    """Remove overlapping metrics found in all_in_one.json from another JSON."""
    for metric_category in ['common_metrics', 'v1_only_metrics', 'v2_only_metrics']:
        if metric_category in all_in_one_data and metric_category in other_json_data:
            for metric in all_in_one_data[metric_category]:
                if metric in other_json_data[metric_category]:
                    del other_json_data[metric_category][metric]

    return other_json_data

def main():
    parser = argparse.ArgumentParser(description='Scrape and compare metrics, then generate reports.')
    parser.add_argument('--v1-endpoint', required=True, help='V1 endpoint URL')
    parser.add_argument('--v2-endpoint', required=True, help='V2 endpoint URL')
    parser.add_argument('--output-dir', required=True, help='Directory to store output files')

    args = parser.parse_args()

    v1_metrics_path = os.path.join(args.output_dir, "V1_Metrics.json")
    v2_metrics_path = os.path.join(args.output_dir, "V2_Metrics.json")
    differences_path = os.path.join(args.output_dir, "differences.json")

    subprocess.run(f"prom2json {args.v1_endpoint}/metrics > {v1_metrics_path}", shell=True, check=True)
    subprocess.run(f"prom2json {args.v2_endpoint}/metrics > {v2_metrics_path}", shell=True, check=True)

    with open(v1_metrics_path, 'r') as file:
        v1_metrics = json.load(file)

    with open(v2_metrics_path, 'r') as file:
        v2_metrics = json.load(file)

    v1_metrics_with_labels = extract_metrics_with_labels(v1_metrics)
    v2_metrics_with_labels = extract_metrics_with_labels(v2_metrics, strip_prefix="otelcol_")

    common_metrics = {}
    v1_only_metrics = {}
    v2_only_metrics = {}

    for name, labels in v1_metrics_with_labels.items():
        if name in v2_metrics_with_labels:
            common_metrics[name] = labels
        elif not name.startswith("jaeger_agent"):
            v1_only_metrics[name] = labels

    for name, labels in v2_metrics_with_labels.items():
        if name not in v1_metrics_with_labels:
            v2_only_metrics[name] = labels

    differences = {
        "common_metrics": common_metrics,
        "v1_only_metrics": v1_only_metrics,
        "v2_only_metrics": v2_only_metrics,
    }

    with open(differences_path, 'w') as file:
        json.dump(differences, file, indent=4)

    print(f"Differences written to {differences_path}")

    md_file = os.path.join(args.output_dir, "metrics_report.md")
    with open(md_file, 'w') as md:
        md.write(f"# Metrics Comparison Report\n\n")
        md.write(f"## Common Metrics\n\n")
        for metric, labels in common_metrics.items():
            md.write(f"### {metric}\n")
            md.write(f"Labels: {json.dumps(labels)}\n\n")

        md.write(f"## V1 Only Metrics\n\n")
        for metric, labels in v1_only_metrics.items():
            md.write(f"### {metric}\n")
            md.write(f"Labels: {json.dumps(labels)}\n\n")

        md.write(f"## V2 Only Metrics\n\n")
        for metric, labels in v2_only_metrics.items():
            md.write(f"### {metric}\n")
            md.write(f"Labels: {json.dumps(labels)}\n\n")

    print(f"Markdown report written to {md_file}")

if __name__ == "__main__":
    main()


