from pathlib import Path
import math

import joblib
import pandas as pd


FEATURE_NAMES = [
    "request_count",
    "error_rate",
    "response_time",
    "cpu_usage",
    "memory_usage",
    "active_connections",
    "network_in",
    "network_out",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "isolation_forest.pkl"
SCALER_PATH = PROJECT_ROOT / "models" / "scaler.pkl"

# Load the saved artifacts once when this module is imported.
if MODEL_PATH.exists() and SCALER_PATH.exists():
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
else:
    model, scaler = None, None


def detect_log(telemetry):
    """Validate telemetry and return a structured anomaly prediction."""
    if model is None or scaler is None:
        raise RuntimeError("Model not trained yet. Run src/model.py first.")
    if not isinstance(telemetry, dict):
        raise ValueError("Telemetry must be a dictionary.")

    missing_fields = [name for name in FEATURE_NAMES if name not in telemetry]
    if missing_fields:
        raise ValueError(f"Missing required telemetry fields: {', '.join(missing_fields)}.")

    feature_values = {}
    for name in FEATURE_NAMES:
        try:
            value = float(telemetry[name])
        except (TypeError, ValueError) as error:
            raise ValueError(f"{name} must be a numeric value.") from error

        if not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number.")
        feature_values[name] = value

    if not 0 <= feature_values["error_rate"] <= 1:
        raise ValueError("error_rate must be between 0 and 1.")

    # Explicit columns preserve the same feature order used during training.
    feature_data = pd.DataFrame([feature_values], columns=FEATURE_NAMES)
    scaled_data = scaler.transform(feature_data)
    prediction = int(model.predict(scaled_data)[0])
    return format_prediction(prediction)


def format_prediction(prediction):
    """Convert an Isolation Forest prediction to the shared API result shape."""
    is_anomaly = prediction == -1

    message = (
        "Anomaly detected: telemetry significantly deviates from the learned baseline."
        if is_anomaly
        else "Normal: telemetry is operating within the learned baseline."
    )
    return {
        "is_anomaly": is_anomaly,
        "prediction": int(prediction),
        "message": message,
    }


if __name__ == "__main__":
    print("LogSentinel Real-Time Guard Active.\n")

    test_logs = [
        {
            "request_count": 140,
            "error_rate": 0.02,
            "response_time": 115.0,
            "cpu_usage": 55.0,
            "memory_usage": 50.0,
            "active_connections": 95,
            "network_in": 17.0,
            "network_out": 14.0,
        },
        {
            "request_count": 1250,
            "error_rate": 0.85,
            "response_time": 2400.0,
            "cpu_usage": 98.0,
            "memory_usage": 96.0,
            "active_connections": 280,
            "network_in": 230.0,
            "network_out": 190.0,
        },
    ]

    for log in test_logs:
        print(f"Checking log: {log}")
        print(detect_log(log))
        print("-" * 50)
