# LogSentinal: Real-Time Server Anomaly Detection

LogSentinel is a Python application that generates synthetic server telemetry, trains an unsupervised Isolation Forest anomaly detector, and serves predictions through a Flask dashboard and JSON API.

![Status](https://img.shields.io/badge/Status-Complete-success)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-lightgrey)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Machine%20Learning-orange)

## Project Structure

```text
log-sentinal/
├── app.py                    # Flask dashboard and prediction API
├── requirements.txt          # Python dependencies
├── data/
│   └── server_logs.csv       # Generated synthetic telemetry
├── models/
│   ├── isolation_forest.pkl  # Trained Isolation Forest
│   └── scaler.pkl            # Fitted StandardScaler
└── src/
    ├── detector.py           # Command-line inference example
    ├── generator.py          # Synthetic log data generator
    └── model.py              # Training and evaluation pipeline
```

The `data/` and `models/` outputs are created by the scripts and do not need to exist before the first run.

## Installation and Setup

Clone the repository and enter its directory:

```powershell
git clone https://github.com/Kaustav5505g/log-sentinal.git
cd log-sentinal
```

Create and activate a virtual environment on Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS or Linux, activate it with:

```sh
python -m venv .venv
source .venv/bin/activate
```

Install the dependencies and run the pipeline from the repository root:

```sh
pip install -r requirements.txt
python src/generator.py
python src/model.py
```

The generator writes `data/server_logs.csv`. The training script evaluates the detector against the synthetic ground-truth labels and saves the model and scaler in `models/`.

## Run the Dashboard

Start the Flask development server after generating the data and training the model:

```sh
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) to inspect traffic values. The dashboard sends predictions to the `POST /predict` endpoint. The API accepts a JSON object with numeric `request_count`, `error_rate`, and `response_time` values and returns an `is_anomaly` boolean and a status message.

## Try the Detector from the Command Line

After training, run the example normal and anomalous samples:

```sh
python src/detector.py
```

## Notes

- The generator creates 1,000 reproducible synthetic records, including approximately 5% labeled anomalies.
- The Isolation Forest is trained without using the ground-truth labels; labels are only used to print evaluation metrics.
- The Flask development server is intended for local testing, not production deployment.

## Skills Demonstrated

- Integrating unsupervised machine learning with a Flask application.
- Generating and preprocessing telemetry data with Pandas and Scikit-Learn.
- Saving and loading model artifacts with `joblib`.
- Structuring data generation, model training, inference, and web routes as separate modules.
