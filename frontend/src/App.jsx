import { useState } from "react";
import "./App.css";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (event) => {
    const file = event.target.files[0];

    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }

    setResult(null);
    setError("");
  };

  const analyzeMedia = async () => {
    if (!selectedFile) {
      setError("Please select an image first.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Analysis failed.");
      }

      setResult(data);

    } catch (error) {
      setError(error.message);

    } finally {
      setLoading(false);
    }
  };


  const getPredictionClass = (prediction) => {
    switch (prediction) {
      case "Authentic":
        return "prediction-authentic";

      case "Probably Authentic":
        return "prediction-probably-authentic";

      case "Needs Manual Review":
        return "prediction-manual-review";

      case "Suspicious":
        return "prediction-suspicious";

      case "High Risk":
        return "prediction-high-risk";

      case "Likely Deepfake":
        return "prediction-likely-deepfake";

      case "Confirmed Manipulation":
        return "prediction-confirmed";

      default:
        return "prediction-default";
    }
  };

  return (
    <div className="app">

      <header className="header">
        <div>
          <h1>AI Media Integrity Detector</h1>

          <p>
            AI Media Integrity, Deepfake Detection and Forensic Reporting System
          </p>
        </div>
      </header>


      <main className="container">

        {/* Upload Section */}

        <section className="upload-card">

          <h2>Digital Media Analysis</h2>

          <p className="description">
            Upload an image to perform digital forensic analysis using
            metadata, Error Level Analysis, noise analysis and copy-move detection.
          </p>

          <div className="upload-box">
            <input
              type="file"
              accept=".jpg,.jpeg,.png"
              onChange={handleFileChange}
            />

            {previewUrl && (
              <div className="image-preview">
                <img
                  src={previewUrl}
                  alt="Selected media preview"
                />
              </div>
            )}

            {selectedFile && (
              <p className="file-name">
                Selected: {selectedFile.name}
              </p>
            )}
          </div>


          <button
            className="analyze-button"
            onClick={analyzeMedia}
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Analyze Media"}
          </button>


          {error && (
            <p className="error-message">
              {error}
            </p>
          )}

        </section>


        {/* Results Section */}

        <section className="results-card">

          <h2>Analysis Results</h2>


          {/* Integrity Score */}

          <div className="score-box">

            <span>Integrity Score</span>

            <strong>
              {result
                ? `${result.result.integrity_score} / 100`
                : "-- / 100"}
            </strong>

            {result && (
              <div className="score-label">
                {result.result.integrity_score >= 95
                  ? "Excellent Integrity"
                  : result.result.integrity_score >= 85
                    ? "Good Integrity"
                    : result.result.integrity_score >= 70
                      ? "Needs Manual Review"
                      : result.result.integrity_score >= 50
                        ? "Suspicious"
                        : "High Risk"}
              </div>
            )}

            {result && (
              <div className="score-progress">
                <div
                  className="score-progress-bar"
                  style={{
                    width: `${result.result.integrity_score}%`,
                    backgroundColor: result.result.color,
                  }}
                ></div>
              </div>
            )}

          </div>


          <div className="prediction">

            <span>Final Assessment</span>

            <strong
              style={{
                color: result ? result.result.color : "#0f5132",
                fontWeight: "bold",
              }}
            >
              {result
                ? result.result.prediction
                : "Waiting for analysis"}
            </strong>

            {result && (
              <p className="prediction-note">
                This assessment is based on the available forensic
                indicators and should not be treated as absolute proof
                of manipulation or AI generation.
              </p>
            )}

          </div>
          {/* Forensic Findings */}

          {result && result.result.reasons && (
            <div className="findings-box">
              <h3>Forensic Findings</h3>

              <ul>
                {result.result.reasons.map((reason, index) => (
                  <li key={index}>
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          )}


          {/* Forensic Results */}

          <div className="forensics">

            {/* EXIF */}
            <div className="forensic-item">

              <h3>EXIF Metadata</h3>

              {result ? (
                <>
                  <p>
                    {Object.keys(result.forensics.exif).length > 0
                      ? "Metadata available"
                      : "No EXIF metadata found"}
                  </p>

                  {Object.keys(result.forensics.exif).length > 0 && (
                    <small>
                      {Object.keys(result.forensics.exif).length} metadata fields found
                    </small>
                  )}
                </>
              ) : (
                <p>Waiting...</p>
              )}

            </div>


            {/* ELA */}
            <div className="forensic-item">

              <h3>ELA Analysis</h3>

              {result ? (
                <>
                  <p>
                    Status: {result.forensics.ela.status || "Completed"}
                  </p>

                  <p>
                    Score: {result.forensics.ela.score ?? "N/A"}
                  </p>

                  <small>
                    {result.forensics.ela.details ||
                      "No additional details."}
                  </small>

                  {result.forensics.ela.report && (
                    <div className="forensic-image">
                      <img
                        src={`http://127.0.0.1:8000/${result.forensics.ela.report.replace(/\\/g, "/")}`}
                        alt="ELA forensic analysis"
                      />
                    </div>
                  )}
                </>
              ) : (
                <p>Waiting...</p>
              )}

            </div>


            {/* Noise */}
            <div className="forensic-item">

              <h3>Noise Analysis</h3>

              {result ? (
                <>
                  <p>
                    Status: {result.forensics.noise.status || "Completed"}
                  </p>

                  <p>
                    Score: {result.forensics.noise.score ?? "N/A"}
                  </p>

                  <small>
                    {result.forensics.noise.details ||
                      "No additional details."}
                  </small>

                  {result.forensics.noise.report && (
                    <div className="forensic-image">
                      <img
                        src={`http://127.0.0.1:8000/${result.forensics.noise.report.replace(/\\/g, "/")}`}
                        alt="Noise forensic analysis"
                      />
                    </div>
                  )}
                </>
              ) : (
                <p>Waiting...</p>
              )}

            </div>


            {/* Copy-Move */}
            <div className="forensic-item">

              <h3>Copy-Move Detection</h3>

              {result ? (
                <>
                  <p>
                    Status: {result.forensics.copy_move.status || "Completed"}
                  </p>

                  <p>
                    Matches: {result.forensics.copy_move.matches ?? 0}
                  </p>

                  <small>
                    {result.forensics.copy_move.details ||
                      "No additional details."}
                  </small>

                  {result.forensics.copy_move.report && (
                    <div className="forensic-image">
                      <img
                        src={`http://127.0.0.1:8000/${result.forensics.copy_move.report.replace(/\\/g, "/")}`}
                        alt="Copy-move forensic analysis"
                      />
                    </div>
                  )}
                </>
              ) : (
                <p>Waiting...</p>
              )}

            </div>

          </div>


          {/* PDF Report Button */}

          {result && result.report && result.report.pdf && (
            <a
              className="report-button"
              href={`http://127.0.0.1:8000/${result.report.pdf.replace(/\\/g, "/")}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              View PDF Report
            </a>
          )}

        </section>

      </main>


      <footer>

        <p>
          AI Media Integrity Detector © 2026
        </p>

      </footer>

    </div>
  );
}

export default App;