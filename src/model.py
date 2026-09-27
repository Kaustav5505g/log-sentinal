import pandas as pd
import joblib
import os
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix


def train_anomaly_detector():
    # 1. Load the dataset
    print("Loading log data...")
    df = pd.read_csv("data/server_logs.csv")

    feature_cols = ["request_count", "error_rate", "response_time"]
    X = df[feature_cols]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("Training Isolation Forest Model...")
    model = IsolationForest(contamination=0.05, random_state=42)

    predictions = model.fit_predict(X_scaled)

    df["predicted_anomaly"] = [1 if p == -1 else 0 for p in predictions]

    print("\n--- Model Evaluation Report ---")
    print(confusion_matrix(df["is_true_anomaly"], df["predicted_anomaly"]))
    print("\nClassification Report:")
    print(
        classification_report(
            df["is_true_anomaly"],
            df["predicted_anomaly"],
            target_names=["Normal", "Anomaly"],
        )
    )

    anomalies_found = df[df["predicted_anomaly"] == 1]
    print(f"\nTotal anomalies detected by LogSentinel: {len(anomalies_found)}")

    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/isolation_forest.pkl")
    joblib.dump(scaler, "models/scaler.pkl")
    print("\nModel and scaler successfully saved to 'models/' directory!")

    return model, scaler


if __name__ == "__main__":
    train_anomaly_detector()