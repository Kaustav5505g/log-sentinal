from pathlib import Path

import numpy as np
import pandas as pd


def generate_server_logs(sample_count=1000, anomaly_fraction=0.05, random_state=42):
    rng = np.random.default_rng(random_state)
    anomaly_count = max(1, round(sample_count * anomaly_fraction))

    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=sample_count, freq="min"),
            "request_count": np.clip(rng.normal(100, 18, sample_count), 20, None),
            "error_rate": rng.beta(1.5, 35, sample_count),
            "response_time": np.clip(rng.normal(180, 35, sample_count), 40, None),
            "is_true_anomaly": np.zeros(sample_count, dtype=int),
        }
    )

    anomaly_indices = rng.choice(sample_count, size=anomaly_count, replace=False)
    df.loc[anomaly_indices, "is_true_anomaly"] = 1

    anomaly_types = rng.integers(0, 3, size=anomaly_count)
    for index, anomaly_type in zip(anomaly_indices, anomaly_types):
        if anomaly_type == 0:
            df.loc[index, "request_count"] = rng.uniform(230, 420)
        elif anomaly_type == 1:
            df.loc[index, "error_rate"] = rng.uniform(0.35, 0.9)
        else:
            df.loc[index, "response_time"] = rng.uniform(500, 1200)

    output_path = Path(__file__).resolve().parent.parent / "data" / "server_logs.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} log rows at {output_path}")
    print(f"Ground-truth anomalies: {anomaly_count}")


if __name__ == "__main__":
    generate_server_logs()