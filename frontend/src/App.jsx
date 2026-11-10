import { useState, useEffect } from "react";

import "./App.css";

import Auth from "./Auth";

import { getApiBaseUrl } from "./services/api";

const API_URL = getApiBaseUrl();

const ALLOWED_EXTENSIONS = [

  ".jpg",

  ".jpeg",

  ".png",

  ".mp4",

  ".avi",

  ".mov",

];

function App() {

  const [currentUser, setCurrentUser] = useState(null);

  const [selectedFile, setSelectedFile] = useState(null);

  const [previewUrl, setPreviewUrl] = useState(null);

  const [result, setResult] = useState(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [history, setHistory] = useState([]);

  const [historyLoading, setHistoryLoading] = useState(false);

  const [showHistory, setShowHistory] = useState(false);

  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);

  const [searchTerm, setSearchTerm] = useState("");

  const [predictionFilter, setPredictionFilter] = useState("All");

  const [profileOpen, setProfileOpen] = useState(false);

  // Show the login/register form without blocking guest access.

  const [showAuth, setShowAuth] = useState(false);

  const [editingProfile, setEditingProfile] = useState(false);

  const [profileName, setProfileName] = useState("");

  // Detect whether the selected file is a video.

  const isVideoFile = (file) => {

    if (!file) return false;

    const extension = file.name

      .slice(file.name.lastIndexOf("."))

      .toLowerCase();

    return (

      file.type.startsWith("video/") ||

      [".mp4", ".avi", ".mov"].includes(extension)

    );

  };

  // Convert backend file paths into browser-accessible URLs.

  const getFileUrl = (path) => {
    if (!path) return "";

    const normalizedPath = String(path)
      .replace(/\\/g, "/")
      .replace(/^\/+/, "");

    return `${API_URL}/${normalizedPath}`;
  };

  // Extract the PDF report path from the backend response.

  const getReportPath = (data) => {

    return (

      data?.report?.pdf ||

      data?.report_path ||

      data?.pdf_report ||

      data?.report_url ||

      data?.result?.report?.pdf ||

      data?.result?.report_path ||

      data?.result?.pdf_report ||

      null

    );

  };

  // Release the currently selected preview URL.

  const clearPreview = () => {

    setPreviewUrl((previousUrl) => {

      if (previousUrl) {

        URL.revokeObjectURL(previousUrl);

      }

      return null;

    });

  };

  // Handle image and video selection.

  const handleFileChange = (event) => {

    const file = event.target.files?.[0];

    setError("");

    setResult(null);

    if (!file) return;

    const extension = file.name

      .slice(file.name.lastIndexOf("."))

      .toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(extension)) {

      setError(

        "Please select a JPG, JPEG, PNG, MP4, AVI, or MOV file."

      );

      event.target.value = "";

      setSelectedFile(null);

      clearPreview();

      return;

    }

    if (file.size === 0) {

      setError("The selected file is empty.");

      event.target.value = "";

      setSelectedFile(null);

      clearPreview();

      return;

    }

    clearPreview();

    setSelectedFile(file);

    setPreviewUrl(URL.createObjectURL(file));

  };

  // Load the logged-in user's analysis history.

  const fetchHistory = async () => {

    if (!currentUser?.access_token) return;

    setHistoryLoading(true);

    try {

      const response = await fetch(`${API_URL}/history/`, {

        headers: {

          Authorization: `Bearer ${currentUser.access_token}`,

        },

      });

      if (response.status === 401) {

        setCurrentUser(null);

        setHistory([]);

        setError("Your login session has expired. Please log in again.");

        return;

      }

      if (!response.ok) {

        throw new Error("Failed to load analysis history.");

      }

      const data = await response.json();

      // Support either a list response or { history: [...] }.

      const records = Array.isArray(data)

        ? data

        : Array.isArray(data.history)

          ? data.history

          : [];

      setHistory(records);

    } catch (err) {

      console.error("History loading error:", err);

      setError(err.message || "Unable to load analysis history.");

    } finally {

      setHistoryLoading(false);

    }

  };

  // Upload and analyze the selected image or video.

  const analyzeMedia = async () => {

    if (!selectedFile) {

      setError("Please select an image or video first.");

      return;

    }

    setLoading(true);

    setError("");

    setResult(null);

    const formData = new FormData();

    formData.append("file", selectedFile);

    try {

      const headers = {};

      // Guests send no Authorization header. Logged-in users send their JWT.

      if (currentUser?.access_token) {

        headers.Authorization = `Bearer ${currentUser.access_token}`;

      }

      const response = await fetch(`${API_URL}/upload/`, {

        method: "POST",

        headers,

        body: formData,

      });

      const data = await response.json();

      if (response.status === 401) {

        setCurrentUser(null);

        setHistory([]);

        throw new Error(

          "Your login session has expired. Please log in again."

        );

      }

      if (!response.ok) {

        throw new Error(

          data.detail || "Media analysis failed."

        );

      }

      setResult(data);

      // Refresh history after successful analysis.

      await fetchHistory();

    } catch (err) {

      console.error("Media analysis error:", err);

      setError(err.message || "An unexpected error occurred.");

    } finally {

      setLoading(false);

    }

  };

  // Load history after login.

  useEffect(() => {

    if (currentUser?.access_token) {

      fetchHistory();

    }

  }, [currentUser]);

  // Release preview memory when the component unmounts.

  useEffect(() => {

    return () => {

      if (previewUrl) {

        URL.revokeObjectURL(previewUrl);

      }

    };

  }, [previewUrl]);

  // Filter history by filename and prediction.

  const filteredHistory = history.filter((item) => {

    const filename = (

      item.original_filename || ""

    ).toLowerCase();

    const matchesSearch = filename.includes(

      searchTerm.toLowerCase().trim()

    );

    const matchesPrediction =

      predictionFilter === "All" ||

      item.prediction === predictionFilter;

    return matchesSearch && matchesPrediction;

  });

  // Assign CSS classes based on the prediction.

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

  // Log out the current user.

  const handleLogout = () => {

    clearPreview();

    setCurrentUser(null);

    setSelectedFile(null);

    setResult(null);

    setHistory([]);

    setShowHistory(false);

    setSelectedHistoryItem(null);

    setSearchTerm("");

    setPredictionFilter("All");

    setError("");

    setProfileOpen(false);

    setShowAuth(false);

  };

  // Show login/registration before displaying the dashboard.

  const analysis = result?.result;

  const exif = result?.forensics?.exif || {};

  const ela = result?.forensics?.ela || {};

  const noise = result?.forensics?.noise || {};

  const copyMove = result?.forensics?.copy_move || {};

  const isVideo = isVideoFile(selectedFile);

  const integrityScore = analysis?.integrity_score;

  const hasIntegrityScore =

    integrityScore !== null &&

    integrityScore !== undefined &&

    integrityScore !== "";

  const reportPath = getReportPath(result);

  // Video details are returned by the backend under forensics.video.
  const videoAnalysis =
    result?.forensics?.video ||
    result?.analysis?.video ||
    result?.video ||
    result?.result?.video ||
    null;

  const videoSummary =
    videoAnalysis?.detection_summary ||
    videoAnalysis?.summary ||
    {};

  const averageFakeProbability =
    videoSummary.average_fake_probability ??
    videoSummary.average_fake_probability_mean ??
    null;

  const frameAnalysis = Array.isArray(videoAnalysis?.frame_analysis)
    ? videoAnalysis.frame_analysis
    : [];

  const failedFrameDetails = Array.isArray(videoAnalysis?.failed_frame_details)
    ? videoAnalysis.failed_frame_details
    : [];

  const provisionalThreshold =
    Number(videoSummary.provisional_classification_threshold ?? 0.5);

  const suspiciousFrames = frameAnalysis.filter((frame) => {
    const probability = Number(frame.fake_probability);
    return Number.isFinite(probability) && probability >= provisionalThreshold;
  });

  const highestScoringFrame =
    videoSummary.highest_scoring_frame ||
    (frameAnalysis.length
      ? frameAnalysis.reduce((highest, frame) =>
        Number(frame.fake_probability) > Number(highest.fake_probability)
          ? frame
          : highest
      )
      : null);

  return (

    <div className="app">

      {/* Header */}

      <header className="header">

        <div>

          <h1>AI Media Integrity Detector</h1>

          <p>

            AI Media Integrity, Deepfake Detection and

            Forensic Reporting System

          </p>

        </div>

        <div className="profile-container">

          {currentUser?.access_token && currentUser?.user ? (

            <>

              <button

                type="button"

                className="profile-icon-button"

                onClick={() => {

                  setProfileOpen(!profileOpen);

                  setEditingProfile(false);

                }}

                aria-label="Open user profile"

                aria-expanded={profileOpen}

              >

                {currentUser.user.name?.charAt(0).toUpperCase() || "U"}

              </button>

              {profileOpen && (

                <div className="profile-dropdown">

                  <h3>My Profile</h3>

                  {!editingProfile ? (

                    <>

                      <div className="profile-info">

                        <strong>{currentUser.user.name}</strong>

                        <small>{currentUser.user.email}</small>

                      </div>

                      <button

                        type="button"

                        className="profile-menu-button"

                        onClick={() => {

                          setProfileName(currentUser.user.name || "");

                          setEditingProfile(true);

                        }}

                      >

                        Edit Profile

                      </button>

                      <button

                        type="button"

                        className="profile-menu-button logout-menu-button"

                        onClick={handleLogout}

                      >

                        Logout

                      </button>

                    </>

                  ) : (

                    <>

                      <label htmlFor="profileName">Name</label>

                      <input

                        id="profileName"

                        type="text"

                        value={profileName}

                        onChange={(event) => setProfileName(event.target.value)}

                      />

                      <p className="profile-note">

                        Name editing requires a backend API to save the change.

                      </p>

                      <button

                        type="button"

                        className="profile-menu-button"

                        onClick={() => setEditingProfile(false)}

                      >

                        Cancel

                      </button>

                    </>

                  )}

                </div>

              )}

            </>

          ) : (

            <button

              type="button"

              className="profile-menu-button"

              onClick={() => setShowAuth(true)}

            >

              Login / Register

            </button>

          )}

        </div>

      </header>

      {showAuth && (

        <div

          className="auth-modal-overlay"

          role="dialog"

          aria-modal="true"

          aria-label="Login or register"

          onClick={(event) => {

            if (event.target === event.currentTarget) setShowAuth(false);

          }}

          style={{

            position: "fixed",

            inset: 0,

            zIndex: 1000,

            background: "rgba(0, 0, 0, 0.6)",

            display: "flex",

            justifyContent: "center",

            alignItems: "center",

            padding: "20px",

            overflowY: "auto",

          }}

        >

          <div

            className="auth-modal-content"

            style={{

              position: "relative",

              width: "100%",

              maxWidth: "520px",

              maxHeight: "90vh",

              overflowY: "auto",

              background: "#ffffff",

              borderRadius: "12px",

              padding: "20px",

            }}

          >

            <button

              type="button"

              aria-label="Close login form"

              onClick={() => setShowAuth(false)}

              style={{

                position: "absolute",

                top: "8px",

                right: "12px",

                zIndex: 2,

                border: "none",

                background: "transparent",

                fontSize: "28px",

                cursor: "pointer",

              }}

            >

              ×

            </button>

            <Auth

              onLogin={(data) => {

                setCurrentUser(data);

                setShowAuth(false);

                setError("");

              }}

            />

          </div>

        </div>

      )}

      <main className="container">

        {/* Upload Section */}

        <section className="upload-card">

          <h2>Digital Media Analysis</h2>

          <p className="description">

            Upload an image or video for digital forensic analysis.

            Images support metadata, Error Level Analysis, noise

            analysis, and copy-move detection. Videos support frame

            extraction and AI-generated-content screening.

          </p>

          <div className="upload-box">

            <input

              type="file"

              accept=".jpg,.jpeg,.png,.mp4,.avi,.mov,image/jpeg,image/png,video/mp4,video/x-msvideo,video/quicktime"

              onChange={handleFileChange}

              disabled={loading}

            />

            {previewUrl && selectedFile && (

              <div className="image-preview">

                {isVideoFile(selectedFile) ? (

                  <video

                    src={previewUrl}

                    controls

                    preload="metadata"

                    style={{

                      width: "100%",

                      maxHeight: "350px",

                      borderRadius: "8px",

                    }}

                  >

                    Your browser does not support video playback.

                  </video>

                ) : (

                  <img

                    src={previewUrl}

                    alt="Selected media preview"

                    style={{

                      maxWidth: "100%",

                      maxHeight: "350px",

                      objectFit: "contain",

                      borderRadius: "8px",

                    }}

                  />

                )}

              </div>

            )}

            {selectedFile && (

              <p className="file-name">

                <strong>Selected:</strong> {selectedFile.name}

                <br />

                <strong>Type:</strong> {isVideo ? "Video" : "Image"}

                <br />

                <strong>Size:</strong>{" "}

                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB

              </p>

            )}

          </div>

          <button

            type="button"

            className="analyze-button"

            onClick={analyzeMedia}

            disabled={loading || !selectedFile}

          >

            {loading ? "Analyzing Media..." : "Analyze Media"}

          </button>

          {loading && (

            <p className="loading-message">

              Please wait while your media is being analyzed.

            </p>

          )}

          {error && (

            <p className="error-message" role="alert">

              {error}

            </p>

          )}

        </section>

        {/* Analysis Results */}

        <section className="results-card">

          <h2>Analysis Results</h2>

          <div className="results-scroll-area">

            {/* Integrity Score */}

            <div className="score-box">

              <span>Integrity Score</span>

              <strong>

                {analysis

                  ? hasIntegrityScore

                    ? `${integrityScore} / 100`

                    : "Not calculated"

                  : "-- / 100"}

              </strong>

              {analysis && hasIntegrityScore && (

                <>

                  <div className="score-label">

                    {isVideo
                      ? "Provisional Video Screening Estimate"
                      : integrityScore >= 95
                        ? "Excellent Integrity"
                        : integrityScore >= 85
                          ? "Good Integrity"
                          : integrityScore >= 70
                            ? "Needs Manual Review"
                            : integrityScore >= 50
                              ? "Suspicious"
                              : "High Risk"}

                  </div>

                  {isVideo && (
                    <p className="prediction-note">
                      This estimate is derived from sampled frame-level model
                      scores. It is not a validated probability of video
                      authenticity or proof of manipulation.
                    </p>
                  )}

                  <div className="score-progress">

                    <div

                      className="score-progress-bar"

                      style={{

                        width: `${Math.max(

                          0,

                          Math.min(100, Number(integrityScore) || 0)

                        )}%`,

                        backgroundColor: analysis.color || "#198754",

                      }}

                    />

                  </div>

                </>

              )}

            </div>

            {/* Final Assessment */}

            <div className="prediction">

              <span>Final Assessment</span>

              <strong

                className={getPredictionClass(analysis?.prediction)}

                style={{

                  color: analysis?.color || "#0f5132",

                  fontWeight: "bold",

                }}

              >

                {analysis?.prediction || "Waiting for analysis"}

              </strong>

              {analysis && (

                <p className="prediction-note">

                  This assessment is based on available forensic

                  indicators. It is not absolute proof of authenticity,

                  manipulation, or AI generation.

                </p>

              )}

            </div>

            {/* Forensic Findings */}

            {analysis?.reasons && (

              <div className="findings-box">

                <h3>Forensic Findings</h3>

                <ul>

                  {analysis.reasons.map((reason, index) => (

                    <li key={index}>{reason}</li>

                  ))}

                </ul>

              </div>

            )}

            {/* Video Analysis */}

            {isVideo && result && (
              <div className="findings-box">
                <h3>Video Analysis</h3>

                <p>
                  Resolution:{" "}
                  {videoAnalysis?.video_width ??
                    videoAnalysis?.width ??
                    "N/A"}{" "}
                  ×{" "}
                  {videoAnalysis?.video_height ??
                    videoAnalysis?.height ??
                    "N/A"}
                </p>

                <p>
                  Frame Rate: {videoAnalysis?.fps ?? "N/A"} FPS
                </p>

                <p>
                  Duration:{" "}
                  {videoAnalysis?.duration_seconds ??
                    videoAnalysis?.duration ??
                    "N/A"}{" "}
                  seconds
                </p>

                <p>
                  Total Video Frames: {videoAnalysis?.total_frames ?? "N/A"}
                </p>

                <p>
                  Frames Extracted:{" "}
                  {videoSummary.frames_extracted ??
                    videoAnalysis?.frames_extracted ??
                    "N/A"}
                </p>

                <p>
                  Frames Analyzed:{" "}
                  {videoSummary.frames_analyzed ??
                    videoAnalysis?.frames_analyzed ??
                    "N/A"}
                </p>

                <p>
                  Frames Failed:{" "}
                  {videoSummary.frames_failed ??
                    videoAnalysis?.frames_failed ??
                    failedFrameDetails.length}
                </p>

                <p>
                  Average AI-Generated-Like Score:{" "}
                  {averageFakeProbability !== null
                    ? `${(Number(averageFakeProbability) * 100).toFixed(2)}%`
                    : "Unavailable"}
                </p>

                <p>
                  Provisional threshold:{" "}
                  {(provisionalThreshold * 100).toFixed(0)}%
                </p>

                <p>
                  Frames above provisional threshold:{" "}
                  {videoSummary.frames_above_provisional_threshold ??
                    suspiciousFrames.length}
                </p>

                <p>
                  AI-generated-like frames:{" "}
                  {videoSummary.ai_generated_like_frames ?? "N/A"}
                </p>

                <p>
                  Highest-scoring frame:{" "}
                  {highestScoringFrame?.frame ??
                    videoSummary.highest_scoring_frame ??
                    "N/A"}
                </p>

                {highestScoringFrame && (
                  <p>
                    Highest frame fake score:{" "}
                    {Number.isFinite(Number(highestScoringFrame.fake_probability))
                      ? `${(Number(highestScoringFrame.fake_probability) * 100).toFixed(2)}%`
                      : Number.isFinite(Number(videoSummary.highest_frame_fake_probability))
                        ? `${(Number(videoSummary.highest_frame_fake_probability) * 100).toFixed(2)}%`
                        : "N/A"}
                  </p>
                )}

                <p>
                  Model: {videoSummary.model || "N/A"}
                </p>

                <p>
                  Analysis status:{" "}
                  {videoSummary.analysis_status || "Unavailable"}
                </p>

                <p className="prediction-note">
                  Frame scores are automated screening estimates. The
                  threshold is provisional and has not been validated as a
                  reliable video-authenticity boundary.
                </p>

                <h3>Frames Requiring Review</h3>

                {suspiciousFrames.length > 0 ? (
                  <ul>
                    {suspiciousFrames.slice(0, 15).map((frame, index) => (
                      <li key={`${frame.frame_number ?? "frame"}-${index}`}>
                        <strong>
                          Frame {frame.frame_number ?? frame.frame ?? index + 1}
                        </strong>
                        {" — "}
                        Time:{" "}
                        {frame.timestamp_seconds != null
                          ? `${Number(frame.timestamp_seconds).toFixed(2)}s`
                          : "N/A"}
                        {" — "}
                        Fake score:{" "}
                        {Number.isFinite(Number(frame.fake_probability))
                          ? `${(Number(frame.fake_probability) * 100).toFixed(2)}%`
                          : "N/A"}
                        {" — "}
                        {frame.prediction || "Unknown"}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No frames crossed the provisional review threshold.</p>
                )}

                {suspiciousFrames.length > 15 && (
                  <p>
                    Showing the first 15 of {suspiciousFrames.length} frames
                    requiring review.
                  </p>
                )}

                {failedFrameDetails.length > 0 && (
                  <>
                    <h3>Frames That Could Not Be Analyzed</h3>
                    <ul>
                      {failedFrameDetails.slice(0, 10).map((frame, index) => (
                        <li key={`${frame.frame_number ?? "failed"}-${index}`}>
                          Frame {frame.frame_number ?? "N/A"}:{" "}
                          {frame.error || "Analysis failed"}
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            )}

            {/* Forensic Results */}

            <div className="forensics">

              {/* EXIF Metadata */}

              <div className="forensic-item">

                <h3>EXIF Metadata</h3>

                {result ? (

                  <>

                    <p>

                      {Object.keys(exif).length > 0

                        ? "Metadata available"

                        : isVideo

                          ? "Image EXIF analysis is not applicable to this video result."

                          : "No EXIF metadata found"}

                    </p>

                    {Object.keys(exif).length > 0 && (

                      <>

                        <small>

                          {Object.keys(exif).length} metadata fields found

                        </small>

                        <ul>

                          {Object.entries(exif)

                            .slice(0, 10)

                            .map(([key, value]) => (

                              <li key={key}>

                                <strong>{key}:</strong> {String(value)}

                              </li>

                            ))}

                        </ul>

                      </>

                    )}

                  </>

                ) : (

                  <p>Waiting...</p>

                )}

              </div>

              {/* ELA Analysis */}

              <div className="forensic-item">

                <h3>ELA Analysis</h3>

                {result ? (

                  <>

                    <p>Status: {ela.status || (isVideo ? "N/A" : "Completed")}</p>

                    <p>Score: {ela.score ?? "N/A"}</p>

                    <small>

                      {ela.details ||

                        (isVideo

                          ? "ELA results are not provided for this video analysis."

                          : "No additional details.")}

                    </small>

                    {ela.report && (

                      <div className="forensic-image">

                        <img

                          src={getFileUrl(ela.report)}

                          alt="ELA forensic analysis"

                        />

                      </div>

                    )}

                  </>

                ) : (

                  <p>Waiting...</p>

                )}

              </div>

              {/* Noise Analysis */}

              <div className="forensic-item">

                <h3>Noise Analysis</h3>

                {result ? (

                  <>

                    <p>Status: {noise.status || (isVideo ? "N/A" : "Completed")}</p>

                    <p>Score: {noise.score ?? "N/A"}</p>

                    <small>

                      {noise.details ||

                        (isVideo

                          ? "Noise analysis results are not provided for this video."

                          : "No additional details.")}

                    </small>

                    {noise.report && (

                      <div className="forensic-image">

                        <img

                          src={getFileUrl(noise.report)}

                          alt="Noise forensic analysis"

                        />

                      </div>

                    )}

                  </>

                ) : (

                  <p>Waiting...</p>

                )}

              </div>

              {/* Copy-Move Detection */}

              <div className="forensic-item">

                <h3>Copy-Move Detection</h3>

                {result ? (

                  <>

                    <p>Status: {copyMove.status || (isVideo ? "N/A" : "Completed")}</p>

                    <p>Matches: {copyMove.matches ?? "N/A"}</p>

                    <small>

                      {copyMove.details ||

                        (isVideo

                          ? "Copy-move analysis results are not provided for this video."

                          : "No additional details.")}

                    </small>

                    {copyMove.report && (

                      <div className="forensic-image">

                        <img

                          src={getFileUrl(copyMove.report)}

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

            {/* PDF Report */}

            {result && (

              <div className="report-section">

                {reportPath ? (

                  <a

                    className="report-button"

                    href={getFileUrl(reportPath)}

                    target="_blank"

                    rel="noopener noreferrer"

                  >

                    📄 View PDF Report

                  </a>

                ) : (

                  <p className="prediction-note">

                    PDF report path was not found in the analysis response.

                  </p>

                )}

              </div>

            )}

          </div>

        </section>

      </main>

      {/* History is available only to authenticated users. */}

      {currentUser?.access_token && (

        <>

          {/* Compact History Section */}

          <section className="history-card">

            <div className="history-header">

              <div>

                <h2>Analysis History</h2>

                <p>View your previous analyses and reports.</p>

              </div>

              <button

                type="button"

                className="history-refresh"

                onClick={() => {

                  setShowHistory(true);

                  setSelectedHistoryItem(null);

                  fetchHistory();

                }}

              >

                View Analysis History ({history.length})

              </button>

            </div>

          </section>

          {/* History Modal */}

          {showHistory && (

            <div

              className="history-modal-overlay"

              onClick={() => {

                setShowHistory(false);

                setSelectedHistoryItem(null);

              }}

            >

              <div

                className="history-modal"

                onClick={(event) => event.stopPropagation()}

              >

                <div className="history-modal-header">

                  <div>

                    <h2>My Analysis History</h2>

                    <p>Your previous media analyses and reports.</p>

                  </div>

                  <button

                    type="button"

                    className="history-close-button"

                    onClick={() => {

                      setShowHistory(false);

                      setSelectedHistoryItem(null);

                    }}

                    aria-label="Close history"

                  >

                    ×

                  </button>

                </div>

                {!selectedHistoryItem ? (

                  <>

                    <div className="history-filters">

                      <input

                        type="text"

                        placeholder="Search by filename..."

                        value={searchTerm}

                        onChange={(event) =>

                          setSearchTerm(event.target.value)

                        }

                      />

                      <select

                        value={predictionFilter}

                        onChange={(event) =>

                          setPredictionFilter(event.target.value)

                        }

                      >

                        <option value="All">All Predictions</option>

                        {[...new Set(

                          history

                            .map((item) => item.prediction)

                            .filter(Boolean)

                        )].map((prediction) => (

                          <option key={prediction} value={prediction}>

                            {prediction}

                          </option>

                        ))}

                      </select>

                      <button

                        type="button"

                        className="history-refresh"

                        onClick={fetchHistory}

                        disabled={historyLoading}

                      >

                        {historyLoading ? "Loading..." : "Refresh"}

                      </button>

                    </div>

                    {historyLoading && history.length === 0 ? (

                      <p>Loading analysis history...</p>

                    ) : filteredHistory.length === 0 ? (

                      <p>No matching analysis records found.</p>

                    ) : (

                      <div className="history-record-list">

                        {filteredHistory.map((item, index) => (

                          <div

                            className="history-record"

                            key={

                              item.id ??

                              `${item.original_filename}-${index}`

                            }

                          >

                            <div className="history-record-info">

                              <h3>

                                {item.original_filename || "Unknown file"}

                              </h3>

                              <p>

                                <strong>Prediction:</strong>{" "}

                                {item.prediction || "Not available"}

                              </p>

                              <p>

                                <strong>Integrity Score:</strong>{" "}

                                {item.integrity_score != null

                                  ? `${item.integrity_score} / 100`

                                  : "Not calculated"}

                              </p>

                              <p>

                                <strong>File Type:</strong>{" "}

                                {item.file_type || "N/A"}

                              </p>

                              <p>

                                <strong>Status:</strong>{" "}

                                {item.status || "N/A"}

                              </p>

                            </div>

                            <div className="history-record-actions">

                              <button

                                type="button"

                                className="history-details-button"

                                onClick={() =>

                                  setSelectedHistoryItem(item)

                                }

                              >

                                View Details

                              </button>

                              {item.report_path && (

                                <a

                                  className="report-button"

                                  href={getFileUrl(item.report_path)}

                                  target="_blank"

                                  rel="noopener noreferrer"

                                >

                                  Open PDF

                                </a>

                              )}

                            </div>

                          </div>

                        ))}

                      </div>

                    )}

                  </>

                ) : (

                  <div className="history-detail-view">

                    <h3>

                      {selectedHistoryItem.original_filename ||

                        "Analysis Details"}

                    </h3>

                    <p>

                      <strong>Record ID:</strong>{" "}

                      {selectedHistoryItem.id ?? "N/A"}

                    </p>

                    <p>

                      <strong>File Type:</strong>{" "}

                      {selectedHistoryItem.file_type || "N/A"}

                    </p>

                    <p>

                      <strong>Prediction:</strong>{" "}

                      {selectedHistoryItem.prediction || "Not available"}

                    </p>

                    <p>

                      <strong>Integrity Score:</strong>{" "}

                      {selectedHistoryItem.integrity_score != null

                        ? `${selectedHistoryItem.integrity_score} / 100`

                        : "Not calculated"}

                    </p>

                    <p>

                      <strong>Status:</strong>{" "}

                      {selectedHistoryItem.status || "N/A"}

                    </p>

                    {selectedHistoryItem.report_path ? (

                      <a

                        className="report-button"

                        href={getFileUrl(selectedHistoryItem.report_path)}

                        target="_blank"

                        rel="noopener noreferrer"

                      >

                        Open PDF Report

                      </a>

                    ) : (

                      <p>No PDF report path is recorded for this analysis.</p>

                    )}

                    <div className="history-detail-actions">

                      <button

                        type="button"

                        className="history-details-button"

                        onClick={() => setSelectedHistoryItem(null)}

                      >

                        Back to History

                      </button>

                    </div>

                  </div>

                )}

              </div>

            </div>

          )}

        </>

      )}

      {/* Footer */}

      <footer>

        <p>AI Media Integrity Detector © 2026</p>

      </footer>

    </div>

  );

}

export default App;
