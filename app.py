from datetime import datetime

from flask import Flask, jsonify, render_template_string, request

from src.detector import FEATURE_NAMES, detect_log, format_prediction


app = Flask(__name__)

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
        .normal { display: block; border: 1px solid #81c784; background: #1a3d2b; color: #ffffff; }
        .anomaly { display: block; border: 1px solid #e57373; background: #3d1a1a; color: #ffffff; }
        .error { display: block; border: 1px solid #e57373; background: #482b25; color: #ffd0b9; }
    </style>
</head>
<body>
    <main>
        <div class="eyebrow">LOGSENTINEL / LIVE MONITOR</div>
        <h1>Traffic Inspector</h1>
        <section class="panel" aria-label="Analyze a server log">
            <form id="logForm" action="/" method="post">
                <label for="request_count">Request count</label>
                <input type="number" id="request_count" name="request_count" min="0" value="{{ values.request_count }}" required>

                <label for="error_rate">Error rate (0.0 to 1.0)</label>
                <input type="number" id="error_rate" name="error_rate" min="0" max="1" step="0.01" value="{{ values.error_rate }}" required>

                <label for="response_time">Response time (ms)</label>
                <input type="number" id="response_time" name="response_time" min="0" step="0.1" value="{{ values.response_time }}" required>

                <label for="cpu_usage">CPU usage (%)</label>
                <input type="number" id="cpu_usage" name="cpu_usage" min="0" max="100" step="0.1" value="{{ values.cpu_usage }}" required>

                <label for="memory_usage">Memory usage (%)</label>
                <input type="number" id="memory_usage" name="memory_usage" min="0" max="100" step="0.1" value="{{ values.memory_usage }}" required>

                <label for="active_connections">Active connections</label>
                <input type="number" id="active_connections" name="active_connections" min="0" step="1" value="{{ values.active_connections }}" required>

                <label for="network_in">Network in</label>
                <input type="number" id="network_in" name="network_in" min="0" step="0.1" value="{{ values.network_in }}" required>

                <label for="network_out">Network out</label>
                <input type="number" id="network_out" name="network_out" min="0" step="0.1" value="{{ values.network_out }}" required>

                <button id="submitButton" type="submit">Analyze log</button>
                {% if result is not none %}
                <div id="resultBox" class="result {{ 'anomaly' if result == -1 else 'normal' }}" role="status" aria-live="polite">
                    {% if result == -1 %}
                    ⚠️ <strong>Anomaly Detected:</strong> Irregular server traffic pattern flagged!
                    {% else %}
                    ✅ <strong>Normal Traffic:</strong> Telemetry metrics are within standard baseline.
                    {% endif %}
                </div>
                {% elif error %}
                <div id="resultBox" class="result error" role="alert">{{ error }}</div>
                {% else %}
                <div id="resultBox" class="result" role="status" aria-live="polite"></div>
                {% endif %}
            </form>
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
                response_time: Number(document.getElementById('response_time').value),
                cpu_usage: Number(document.getElementById('cpu_usage').value),
                memory_usage: Number(document.getElementById('memory_usage').value),
                active_connections: Number(document.getElementById('active_connections').value),
                network_in: Number(document.getElementById('network_in').value),
                network_out: Number(document.getElementById('network_out').value)
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


def classify_log(values):
    """Keep the app-facing entry point while delegating inference to the detector."""
    return detect_log(values)


@app.route("/", methods=["GET", "POST"])
def home():
    values = {
        "request_count": "150",
        "error_rate": "0.03",
        "response_time": "120.0",
        "cpu_usage": "55.0",
        "memory_usage": "50.0",
        "active_connections": "95",
        "network_in": "17.0",
        "network_out": "14.0",
    }
    result = None
    error = None
    status_code = 200

    if request.method == "POST":
        values = {name: request.form.get(name, "") for name in FEATURE_NAMES}
        try:
            numeric_values = {name: float(values[name]) for name in FEATURE_NAMES}
            result = classify_log(numeric_values)["prediction"]
        except RuntimeError as exception:
            error = str(exception)
            status_code = 503
        except (TypeError, ValueError) as exception:
            error = str(exception)
            status_code = 400

    page = render_template_string(
        HOME_TEMPLATE, values=values, result=result, error=error
    )
    return page, status_code


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify the service is running."""
    return {"status": "healthy", "service": "LogSentinel"}, 200


@app.route("/predict", methods=["POST"])
def predict():
    content = request.get_json(silent=True)
    if not isinstance(content, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    try:
        detection = classify_log(content)
        timestamp = datetime.now().isoformat(timespec="microseconds")
        app.logger.info("Telemetry evaluated at %s", timestamp)
        # Preserve compatibility with callers that patch the old classifier to an integer.
        if isinstance(detection, int):
            detection = format_prediction(detection)
        return jsonify(detection)
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 500
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)