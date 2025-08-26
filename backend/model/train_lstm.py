import os
os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (
    mean_squared_error, confusion_matrix, ConfusionMatrixDisplay,
    r2_score, mean_absolute_error, accuracy_score,
    precision_score, recall_score, f1_score, classification_report
)
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.callbacks import EarlyStopping
import joblib

# ---------------- CONFIG PATHS ---------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../.."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "Rain_data.csv")

MODEL_PATH_KERAS = os.path.join(BASE_DIR, "rainfall_lstm.keras")   # modern format
MODEL_PATH_H5 = os.path.join(BASE_DIR, "lstm_model.h5")            # legacy format
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")

PLOTS_DIR = os.path.join(BASE_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)   # Create folder if missing

# ---------------- LOAD DATA ---------------- #
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Rain_data.csv not found at {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

# Use ANNUAL rainfall column
if "ANNUAL" not in df.columns:
    raise ValueError("CSV must contain 'ANNUAL' column")

rainfall = df["ANNUAL"].values.reshape(-1, 1)

# Scale data
scaler = MinMaxScaler(feature_range=(0, 1))
rainfall_scaled = scaler.fit_transform(rainfall)

# Save scaler
joblib.dump(scaler, SCALER_PATH)

# ---------------- CREATE DATASETS ---------------- #
def create_dataset(data, time_step=10):
    X, y = [], []
    for i in range(len(data) - time_step):
        X.append(data[i:i + time_step, 0])
        y.append(data[i + time_step, 0])
    return np.array(X), np.array(y)

time_step = 10
X, y = create_dataset(rainfall_scaled, time_step)
X = X.reshape(X.shape[0], X.shape[1], 1)

# Train-test split
train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

# ---------------- BUILD MODEL ---------------- #
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(time_step, 1)))
model.add(Dropout(0.2))
model.add(LSTM(50, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(1))

model.compile(optimizer="adam", loss="mean_squared_error")

# ---------------- TRAIN ---------------- #
early_stop = EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)

history = model.fit(
    X_train, y_train,
    validation_data=(X_test, y_test),
    epochs=30,
    batch_size=32,
    verbose=1,
    callbacks=[early_stop]
)

# ---------------- SAVE MODEL ---------------- #
# Save in both keras (.keras) and legacy H5 (.h5) formats
model.save(MODEL_PATH_KERAS)
model.save(MODEL_PATH_H5)

print(f"✅ Model saved at:\n  - {MODEL_PATH_KERAS}\n  - {MODEL_PATH_H5}")

# ---------------- PREDICTIONS ---------------- #
y_pred = model.predict(X_test)

# Inverse transform
y_test_inv = scaler.inverse_transform(y_test.reshape(-1, 1))
y_pred_inv = scaler.inverse_transform(y_pred)

# ---------------- EVALUATION ---------------- #
mse = mean_squared_error(y_test_inv, y_pred_inv)
mae = mean_absolute_error(y_test_inv, y_pred_inv)
r2 = r2_score(y_test_inv, y_pred_inv)

print(f"Mean Squared Error (MSE): {mse:.4f}")
print(f"Mean Absolute Error (MAE): {mae:.4f}")
print(f"R² Score: {r2:.4f}")

# --- Plot Loss Curve --- #
plt.figure(figsize=(8, 5))
plt.plot(history.history["loss"], label="Train Loss")
plt.plot(history.history["val_loss"], label="Validation Loss")
plt.title("LSTM Training vs Validation Loss")
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.legend()
plt.savefig(os.path.join(PLOTS_DIR, "loss_curve.png"), dpi=300, bbox_inches="tight")
plt.close()

# --- Plot Actual vs Predicted --- #
plt.figure(figsize=(10, 5))
plt.plot(y_test_inv, label="Actual Annual Rainfall", color="blue")
plt.plot(y_pred_inv, label="Predicted Annual Rainfall", color="red")
plt.title("Actual vs Predicted Annual Rainfall")
plt.xlabel("Samples")
plt.ylabel("Rainfall (mm)")
plt.legend()
plt.savefig(os.path.join(PLOTS_DIR, "actual_vs_pred.png"), dpi=300, bbox_inches="tight")
plt.close()

# --- Confusion Matrix (Categorical Rainfall Levels) --- #
def categorize_rainfall(values):
    categories = []
    for val in values:
        if val < 200:       # Adjust thresholds as per dataset
            categories.append("Low")
        elif val < 1000:
            categories.append("Moderate")
        elif val < 2000:
            categories.append("High")
        else:
            categories.append("Very High")
    return categories

y_test_cat = categorize_rainfall(y_test_inv.flatten())
y_pred_cat = categorize_rainfall(y_pred_inv.flatten())

cm = confusion_matrix(y_test_cat, y_pred_cat, labels=["Low", "Moderate", "High", "Very High"])
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Low", "Moderate", "High", "Very High"])
disp.plot(cmap=plt.cm.Blues, values_format="d")
plt.title("Confusion Matrix (Annual Rainfall Categories)")
plt.savefig(os.path.join(PLOTS_DIR, "confusion_matrix.png"), dpi=300, bbox_inches="tight")
plt.close()

# ---------------- CLASSIFICATION METRICS ---------------- #
accuracy = accuracy_score(y_test_cat, y_pred_cat)
precision = precision_score(y_test_cat, y_pred_cat, average="weighted", zero_division=0)
recall = recall_score(y_test_cat, y_pred_cat, average="weighted", zero_division=0)
f1 = f1_score(y_test_cat, y_pred_cat, average="weighted", zero_division=0)

print("\n--- Classification Metrics (Rainfall Categories) ---")
print(f"Accuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1-score:  {f1:.4f}")

print("\nClassification Report:")
print(classification_report(y_test_cat, y_pred_cat, zero_division=0))

# ---------------- SAVE METRICS TO JSON ---------------- #
metrics = {
    "MSE": float(mse),
    "MAE": float(mae),
    "R2": float(r2),
    "Accuracy": float(accuracy),
    "Precision": float(precision),
    "Recall": float(recall),
    "F1-score": float(f1)
}

with open(os.path.join(BASE_DIR, "metrics.json"), "w") as f:
    json.dump(metrics, f, indent=4)

print(f"\n✅ Metrics saved to {os.path.join(BASE_DIR, 'metrics.json')}")
print(f"✅ Plots saved to {PLOTS_DIR}")
