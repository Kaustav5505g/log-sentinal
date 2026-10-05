from pathlib import Path

import numpy as np
import pandas as pd


def generate_server_logs(sample_count=1000, anomaly_fraction=0.05, random_state=42):
    rng = np.random.default_rng(random_state)
    anomaly_count = max(1, round(sample_count * anomaly_fraction))

    # A small daily pattern makes traffic vary gradually over time.
    time_of_day = np.arange(sample_count) % 1440
    daily_pattern = 18 * np.sin(2 * np.pi * (time_of_day - 360) / 1440)
    request_count = np.clip(
        100 + daily_pattern + rng.normal(0, 15, sample_count), 20, None
    )
    system_load = rng.normal(0, 1, sample_count)
    active_connections = np.clip(
        request_count * 0.7 + rng.normal(0, 8, sample_count), 5, None
    )
    cpu_usage = np.clip(
        15 + request_count * 0.3 + system_load * 5 + rng.normal(0, 4, sample_count),
        5,
        95,
    )
    memory_usage = np.clip(
        35 + request_count * 0.08 + system_load * 3 + rng.normal(0, 2, sample_count),
        10,
        90,
    )
    network_in = np.clip(
        request_count * 0.12 + rng.normal(0, 2, sample_count), 0.1, None
    )
    network_out = np.clip(
        request_count * 0.1 + rng.normal(0, 2, sample_count), 0.1, None
    )

    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=sample_count, freq="min"),
            "request_count": request_count,
            "error_rate": rng.beta(1.5, 35, sample_count),
            "response_time": np.clip(
                125
                + cpu_usage * 0.9
                + system_load * 8
                + rng.normal(0, 15, sample_count),
                40,
                None,
            ),
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "active_connections": active_connections,
            "network_in": network_in,
            "network_out": network_out,
            "is_true_anomaly": np.zeros(sample_count, dtype=int),
        }
    )

    anomaly_indices = rng.choice(sample_count, size=anomaly_count, replace=False)
    df.loc[anomaly_indices, "is_true_anomaly"] = 1

    anomaly_types = rng.integers(0, 4, size=anomaly_count)
    for index, anomaly_type in zip(anomaly_indices, anomaly_types):
        if anomaly_type == 0:
            request_spike = rng.uniform(250, 420)
            df.loc[index, "request_count"] = request_spike
            df.loc[index, "active_connections"] = request_spike * rng.uniform(0.75, 0.95)
            df.loc[index, "cpu_usage"] = rng.uniform(65, 90)
            df.loc[index, "network_in"] = request_spike * rng.uniform(0.14, 0.2)
            df.loc[index, "network_out"] = request_spike * rng.uniform(0.12, 0.18)
            df.loc[index, "response_time"] = rng.uniform(250, 500)
        elif anomaly_type == 1:
            df.loc[index, "error_rate"] = rng.uniform(0.35, 0.9)
            df.loc[index, "response_time"] = rng.uniform(300, 700)
            df.loc[index, "cpu_usage"] = rng.uniform(50, 80)
        elif anomaly_type == 2:
            df.loc[index, "cpu_usage"] = rng.uniform(90, 99)
            df.loc[index, "memory_usage"] = rng.uniform(90, 99)
            df.loc[index, "active_connections"] = rng.uniform(150, 300)
            df.loc[index, "response_time"] = rng.uniform(500, 1000)
        else:
            df.loc[index, "response_time"] = rng.uniform(500, 1200)
            df.loc[index, "cpu_usage"] = rng.uniform(65, 90)
            df.loc[index, "active_connections"] *= rng.uniform(1.3, 1.8)

    output_path = Path(__file__).resolve().parent.parent / "data" / "server_logs.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} log rows at {output_path}")
    print(f"Ground-truth anomalies: {anomaly_count}")


if __name__ == "__main__":
    generate_server_logs()