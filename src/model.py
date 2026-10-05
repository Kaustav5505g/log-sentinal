import pandas as pd
import joblib
import os
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


def train_anomaly_detector():
    # 1. Load the dataset
    print("Loading log data...")
    df = pd.read_csv("data/server_logs.csv")

    feature_cols = [
        "request_count",
        "error_rate",
        "response_time",
        "cpu_usage",
        "memory_usage",
        "active_connections",
        "network_in",
        "network_out",
    ]
    X = df[feature_cols]
    y = df["is_true_anomaly"]

    # Split first so information from the test set cannot affect preprocessing or training.
    X_train, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Learn scaling parameters from training data only, then apply them to both sets.
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("Training Isolation Forest Model...")
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X_train_scaled)

    # Isolation Forest uses -1 for anomalies and 1 for normal observations.
    raw_predictions = model.predict(X_test_scaled)
    predictions = [1 if prediction == -1 else 0 for prediction in raw_predictions]

    print("\n--- Model Evaluation Report ---")
    print(confusion_matrix(y_test, predictions, labels=[0, 1]))
    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            target_names=["Normal", "Anomaly"],
            zero_division=0,
        )
    )

    print(f"Total test samples: {len(y_test)}")
    print(f"Actual anomalies in test set: {int(y_test.sum())}")
    print(f"Predicted anomalies in test set: {sum(predictions)}")

    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/isolation_forest.pkl")
    joblib.dump(scaler, "models/scaler.pkl")
    print("\nModel and scaler successfully saved to 'models/' directory!")

    return model, scaler


if __name__ == "__main__":
    train_anomaly_detector()