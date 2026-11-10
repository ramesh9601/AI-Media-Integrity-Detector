import os

import numpy as np
import onnxruntime as ort
from PIL import Image


# Locate the trained ONNX model.
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "deepfake_model.onnx"
)


# Load the model using CPU execution.
session = ort.InferenceSession(
    MODEL_PATH,
    providers=["CPUExecutionProvider"]
)

INPUT_NAME = session.get_inputs()[0].name


def preprocess_image(image_path):
    """
    Prepare an image using the model's documented preprocessing.
    """

    with Image.open(image_path) as image:
        image = image.convert("RGB")

    width, height = image.size

    # Resize the shortest edge to 440 pixels.
    scale = 440 / min(width, height)

    new_width = int(width * scale)
    new_height = int(height * scale)

    image = image.resize(
        (new_width, new_height),
        Image.Resampling.BICUBIC
    )

    # Center crop to 384 x 384.
    left = (new_width - 384) // 2
    top = (new_height - 384) // 2

    image = image.crop(
        (left, top, left + 384, top + 384)
    )

    # Convert pixels to float32 and normalize.
    array = np.asarray(
        image,
        dtype=np.float32
    ) / 255.0

    mean = np.array(
        [0.4815, 0.4578, 0.4081],
        dtype=np.float32
    )

    std = np.array(
        [0.2686, 0.2613, 0.2758],
        dtype=np.float32
    )

    array = (array - mean) / std

    # Convert HWC to NCHW format.
    array = np.transpose(array, (2, 0, 1))

    # Add the batch dimension.
    array = np.expand_dims(array, axis=0)

    return np.ascontiguousarray(array, dtype=np.float32)


def detect_deepfake_image(image_path):
    """
    Estimate whether an image resembles AI-generated imagery.

    This model is not a universal detector for all deepfakes.
    """

    if not os.path.isfile(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    input_tensor = preprocess_image(image_path)

    outputs = session.run(
        None,
        {INPUT_NAME: input_tensor}
    )

    logit = float(outputs[0][0][0])

    # Convert the model's single logit into a probability.
    if logit >= 0:
        fake_probability = 1.0 / (
            1.0 + np.exp(-logit)
        )
    else:
        exp_value = np.exp(logit)
        fake_probability = exp_value / (
            1.0 + exp_value
        )

    real_probability = 1.0 - fake_probability

    # A provisional threshold, not a validated accuracy guarantee.
    prediction = (
        "AI-Generated-Like"
        if fake_probability >= 0.5
        else "Real-Looking"
    )

    return {
    "status": "Completed",
    "prediction": prediction,
    "fake_probability": round(float(fake_probability), 8),
    "real_probability": round(float(real_probability), 8),
    "model": "CommunityForensics-DeepfakeDet-ViT",
    "analysis_type": "AI-generated image detection",
    "warning": (
        "These are model scores, not proof of authenticity. "
        "The scores have not been established as calibrated probabilities. "
        "Performance on face swaps, manipulated videos, and "
        "unseen generators is not guaranteed."
    )
}