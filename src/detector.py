import time

import joblib
import pandas as pd


def detect_live_log(request_count, error_rate, response_time):
    model = joblib.load("models/isolation_forest.pkl")
    scaler = joblib.load("models/scaler.pkl")

    new_data = pd.DataFrame(
        [
            {
                "request_count": request_count,
                "error_rate": error_rate,
                "response_time": response_time,
            }
        ]
    )

    scaled_data = scaler.transform(new_data)
    prediction = model.predict(scaled_data)[0]

    if prediction == -1:
        return "[ALERT 🚨] Anomaly Detected! Potential attack or server failure."
    return "[NORMAL ✅] Traffic is operating under normal parameters."


if __name__ == "__main__":
    print("LogSentinel Real-Time Guard Active...\n")

    test_logs = [
        {"request_count": 140, "error_rate": 0.02, "response_time": 115.0},
        {"request_count": 1250, "error_rate": 0.85, "response_time": 2400.0},
    ]

    for log in test_logs:
        print(f"Checking log: {log}")
        result = detect_live_log(
            log["request_count"], log["error_rate"], log["response_time"]
        )
        print(result)
        print("-" * 50)
        time.sleep(1)