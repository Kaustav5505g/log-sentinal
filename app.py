import math
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, render_template_string, request


app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "models" / "isolation_forest.pkl"
SCALER_PATH = PROJECT_ROOT / "models" / "scaler.pkl"

if MODEL_PATH.exists() and SCALER_PATH.exists():
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
else:
    model, scaler = None, None

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>LogSentinel Dashboard</title>
    <style>
        :root {
            color-scheme: dark;
            font-family: "Segoe UI", sans-serif;
            background: #101715;
            color: #edf4ef;
        }
        * { box-sizing: border-box; }
        body {
            min-height: 100vh;
            margin: 0;
            padding: 48px 20px;
            background: linear-gradient(135deg, #101715, #1a2922 58%, #172320);
        }
        main { width: min(100%, 540px); margin: 0 auto; }
        .eyebrow { color: #9bc9a8; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.12em; }
        h1 { margin: 8px 0 24px; font-size: clamp(1.8rem, 8vw, 2.5rem); }
        .panel {
            padding: 24px;
            border: 1px solid #3a5145;
            border-radius: 8px;
            background: #1b2822;
            box-shadow: 0 18px 50px #050a0870;
        }
        label { display: block; margin: 16px 0 7px; color: #c0d0c5; font-size: 0.9rem; }
        input, button { width: 100%; min-height: 44px; border-radius: 5px; font: inherit; }
        input { padding: 10px 12px; border: 1px solid #455b4d; background: #111a16; color: #f4faf5; }
        input:focus { outline: 2px solid #8fc79e; outline-offset: 2px; }
        button { margin-top: 22px; border: 0; background: #a6d7a9; color: #142019; font-weight: 700; cursor: pointer; }
        button:hover { background: #bde8bf; }
        button:disabled { cursor: wait; opacity: 0.7; }
        .result { display: none; margin-top: 18px; padding: 14px; border-radius: 5px; line-height: 1.45; }
        .normal { display: block; background: #193c2e; color: #b4e7c9; }
        .anomaly { display: block; background: #482b25; color: #ffd0b9; }
        .error { display: block; background: #482b25; color: #ffd0b9; }
    </style>
</head>
<body>
    <main>
        <div class="eyebrow">LOGSENTINEL / LIVE MONITOR</div>
        <h1>Traffic Inspector</h1>
        <section class="panel" aria-label="Analyze a server log">
            <form id="logForm">
                <label for="request_count">Request count</label>
                <input type="number" id="request_count" min="0" value="150" required>

                <label for="error_rate">Error rate (0.0 to 1.0)</label>
                <input type="number" id="error_rate" min="0" max="1" step="0.01" value="0.03" required>

                <label for="response_time">Response time (ms)</label>
                <input type="number" id="response_time" min="0" step="0.1" value="120.0" required>

                <button id="submitButton" type="submit">Analyze log</button>
            </form>
            <div id="resultBox" class="result" role="status" aria-live="polite"></div>
        </section>
    </main>
    <script>
        document.getElementById('logForm').addEventListener('submit', async (event) => {
            event.preventDefault();
            const button = document.getElementById('submitButton');
            const box = document.getElementById('resultBox');
            const data = {
                request_count: Number(document.getElementById('request_count').value),
                error_rate: Number(document.getElementById('error_rate').value),
                response_time: Number(document.getElementById('response_time').value)
            };

            button.disabled = true;
            box.className = 'result';
            box.textContent = 'Analyzing...';
            box.style.display = 'block';
            try {
                const response = await fetch('/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                if (!response.ok) throw new Error(result.error || 'Analysis failed.');
                box.className = 'result ' + (result.is_anomaly ? 'anomaly' : 'normal');
                box.textContent = result.message;
            } catch (error) {
                box.className = 'result error';
                box.textContent = error.message;
            } finally {
                button.disabled = false;
            }
        });
    </script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HOME_TEMPLATE)


@app.route("/predict", methods=["POST"])
def predict():
    if model is None or scaler is None:
        return jsonify({"error": "Model not trained yet. Run src/model.py first."}), 500

    content = request.get_json(silent=True)
    if not isinstance(content, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    feature_names = ["request_count", "error_rate", "response_time"]
    try:
        values = {name: float(content[name]) for name in feature_names}
        if not all(math.isfinite(value) for value in values.values()):
            raise ValueError("Feature values must be finite numbers.")
        if not 0 <= values["error_rate"] <= 1:
            raise ValueError("error_rate must be between 0 and 1.")

        log_data = pd.DataFrame([values], columns=feature_names)
        scaled = scaler.transform(log_data)
        prediction = model.predict(scaled)[0]
        is_anomaly = bool(prediction == -1)
        message = (
            "🚨 ANOMALY DETECTED: Potential attack or server failure!"
            if is_anomaly
            else "✅ NORMAL: Traffic is operating safely."
        )
        return jsonify({"is_anomaly": is_anomaly, "message": message})
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)