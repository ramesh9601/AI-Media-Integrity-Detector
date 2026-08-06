import cv2
import os


def detect_noise(image_path):

    image = cv2.imread(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    noise = cv2.Laplacian(gray, cv2.CV_64F)

    noise = cv2.convertScaleAbs(noise)

    output_name = "NOISE_" + os.path.basename(image_path)

    output_path = os.path.join("reports", output_name)

    cv2.imwrite(output_path, noise)

    return output_path