import os
import time
import joblib
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename

# ------------------ CONFIG ------------------
UPLOAD_FOLDER = "static/uploads"
RESULT_FOLDER = "static/results"
ALLOWED_EXTENSIONS = {"csv"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# ------------------ LOAD MODEL ------------------
model_path = "src/train_data/rr_model.pkl"
model = joblib.load(model_path)

# ------------------ FLASK APP ------------------
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["RESULT_FOLDER"] = RESULT_FOLDER

# ------------------ HELPERS ------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------ ROUTES ------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"success": False, "error": "Model not loaded on server."}), 500

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ts = int(time.time())
        upload_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{ts}_{filename}")
        file.save(upload_path)

        # Read CSV
        try:
            df = pd.read_csv(upload_path)
        except Exception as e:
            return jsonify({"success": False, "error": f"Error reading CSV: {e}"}), 400

        # Expected columns
        expected_cols = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]

        missing = [c for c in expected_cols if c not in df.columns]
        if missing:
            return jsonify({
                "success": False,
                "error": f"Missing columns: {missing}. Expected: {expected_cols}"
            }), 400

        # Prediction only 0/1
        X = df[expected_cols]
        try:
            preds = model.predict(X)
        except Exception as e:
            return jsonify({"success": False, "error": f"Prediction failed: {e}"}), 500

        df["is_fraud"] = preds.astype(int)

        # Fraud rows
        fraud_rows = df[df["is_fraud"] == 1].copy()
        fraud_rows.reset_index(inplace=True)

        # Save results
        out_ts = int(time.time())
        out_name = f"predictions_{out_ts}.csv"
        out_path = os.path.join(app.config["RESULT_FOLDER"], out_name)
        try:
            df.to_csv(out_path, index=False)
        except Exception as e:
            return jsonify({"success": False, "error": f"Failed to save output CSV: {e}"}), 500

        fraud_list = []
        for _, row in fraud_rows.iterrows():
            orig_index = int(row["index"])
            fraud_list.append({
                "serial_no": orig_index + 1
            })

        response = {
            "success": True,
            "fraud_count": len(fraud_list),
            "fraud_list": fraud_list,
            "result_csv": url_for("static", filename=f"results/{out_name}", _external=True)
        }

        return jsonify(response)

    return jsonify({"success": False, "error": "Upload only CSV files"}), 400

# Download file (optional)
@app.route("/download/<path:filename>")
def downloaded_file(filename):
    return send_from_directory(app.config["RESULT_FOLDER"], filename, as_attachment=True)

# Run server
if __name__ == "__main__":
    app.run(debug=True)
