
from detectors.video_preprocessor import analyze_video

video_path = input("Enter the full path of your video: ")

try:
    result = analyze_video(video_path)

    print("\n--- VIDEO ANALYSIS RESULTS ---")
    print("Width:", result["video_width"])
    print("Height:", result["video_height"])
    print("FPS:", result["fps"])
    print("Total frames:", result["total_frames"])
    print("Duration:", result["duration_seconds"], "seconds")
    print("Extracted frames:", result["frames_extracted"])
    print("Analysis:", result["message"])

except Exception as error:
    print("Error:", error)
