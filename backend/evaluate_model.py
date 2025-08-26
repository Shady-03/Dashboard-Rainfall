import os
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, precision_score, recall_score, f1_score
from keras.models import load_model
import joblib

# Set base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "Rain_data.csv")
RESULTS_PATH = os.path.join(BASE_DIR, "..", "data", "actual_vs_predicted.csv")
METRICS_PATH = os.path.join(BASE_DIR, "..", "data", "metrics.csv")

# Load dataset
df = pd.read_csv(DATA_PATH)

# Select only the column you used for training
values = df["ANNUAL"].values.reshape(-1, 1)

# Load scaler and model
scaler = joblib.load(os.path.join(BASE_DIR, "model", "scaler.pkl"))
model = load_model(os.path.join(BASE_DIR, "model", "lstm_model.h5"))

# Scale the values
values_scaled = scaler.transform(values)

# Create sequences (same as training)
sequence_length = 10
X, y = [], []
for i in range(len(values_scaled) - sequence_length):
    X.append(values_scaled[i:i+sequence_length])
    y.append(values_scaled[i+sequence_length])
X, y = np.array(X), np.array(y)

# Predict
y_pred = model.predict(X)

# Inverse scale
y_true = scaler.inverse_transform(y.reshape(-1, 1))
y_pred_rescaled = scaler.inverse_transform(y_pred)

# Save results
results = pd.DataFrame({
    "Actual_Rainfall": y_true.flatten(),
    "Predicted_Rainfall": y_pred_rescaled.flatten()
})
results.to_csv(RESULTS_PATH, index=False)

# Calculate metrics
mse = mean_squared_error(y_true, y_pred_rescaled)
rmse = np.sqrt(mse)
mae = mean_absolute_error(y_true, y_pred_rescaled)
r2 = r2_score(y_true, y_pred_rescaled)

# Classification-like metrics
y_true_cls = np.round(y_true).astype(int)
y_pred_cls = np.round(y_pred_rescaled).astype(int)

accuracy = accuracy_score(y_true_cls, y_pred_cls)
precision = precision_score(y_true_cls, y_pred_cls, average="weighted", zero_division=0)
recall = recall_score(y_true_cls, y_pred_cls, average="weighted", zero_division=0)
f1 = f1_score(y_true_cls, y_pred_cls, average="weighted", zero_division=0)

metrics = {
    "MSE": mse,
    "RMSE": rmse,
    "MAE": mae,
    "R2": r2,
    "Accuracy": accuracy,
    "Precision": precision,
    "Recall": recall,
    "F1-score": f1
}
pd.DataFrame([metrics]).to_csv(METRICS_PATH, index=False)

print("✅ Evaluation complete. Files saved in data/")

