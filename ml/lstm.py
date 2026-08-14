"""LSTM model definition and training utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any


MODEL_DIR = Path("ml") / "models"


def tensorflow_available() -> bool:
    """Return whether TensorFlow/Keras is available in the environment."""
    try:
        import tensorflow  # noqa: F401
    except ImportError:
        return False
    return True


def build_lstm_model(window_size: int = 24) -> Any:
    """Build a small Keras LSTM model for price prediction."""
    from tensorflow.keras.layers import LSTM, Dense, Input
    from tensorflow.keras.models import Sequential

    model = Sequential(
        [
            Input(shape=(window_size, 1)),
            LSTM(32, return_sequences=False),
            Dense(16, activation="relu"),
            Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


def train_model(
    sequences: list[list[float]],
    targets: list[float],
    window_size: int = 24,
    epochs: int = 5,
) -> Any:
    """Train and return an LSTM model from normalized sequences."""
    if not tensorflow_available():
        raise RuntimeError("TensorFlow is not installed.")

    import numpy as np

    model = build_lstm_model(window_size)
    x_train = np.array(sequences).reshape((len(sequences), window_size, 1))
    y_train = np.array(targets)
    model.fit(x_train, y_train, epochs=epochs, verbose=0)
    return model


def save_model(model: Any, symbol: str) -> Path:
    """Save a trained model to disk."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    path = MODEL_DIR / f"{symbol.upper()}_lstm.keras"
    model.save(path)
    return path


def load_model(symbol: str) -> Any | None:
    """Load a trained model from disk when TensorFlow and the file exist."""
    path = MODEL_DIR / f"{symbol.upper()}_lstm.keras"
    if not path.exists() or not tensorflow_available():
        return None

    from tensorflow.keras.models import load_model as keras_load_model

    return keras_load_model(path)
