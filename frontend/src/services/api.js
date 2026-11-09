
const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * Build request headers.
 * Do not set Content-Type manually for FormData;
 * the browser adds the required multipart boundary.
 */
function getHeaders(token, isFormData = false) {
    const headers = {};

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    if (!isFormData) {
        headers.Accept = "application/json";
    }

    return headers;
}

/**
 * Parse API responses and return helpful error messages.
 */
async function handleResponse(response) {
    const contentType = response.headers.get("content-type") || "";

    const data = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

    if (!response.ok) {
        const message =
            typeof data === "object" && data !== null
                ? data.detail || data.message || "Request failed."
                : data || "Request failed.";

        throw new Error(message);
    }

    return data;
}

/**
 * Upload and analyze an image or video.
 */
export async function uploadMedia(file, token) {
    if (!file) {
        throw new Error("Please select a media file.");
    }

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/upload/`, {
        method: "POST",
        headers: getHeaders(token, true),
        body: formData,
    });

    return handleResponse(response);
}

/**
 * Retrieve the authenticated user's analysis history.
 */
export async function getAnalysisHistory(token) {
    const response = await fetch(`${API_BASE_URL}/history/`, {
        method: "GET",
        headers: getHeaders(token),
    });

    return handleResponse(response);
}

/**
 * Convert a backend-relative file path to a browser URL.
 */
export function getMediaUrl(path) {
    if (!path) {
        return "";
    }

    const normalizedPath = String(path)
        .replace(/\\/g, "/")
        .replace(/^\/+/, "");

    return `${API_BASE_URL}/${normalizedPath}`;
}

/**
 * Return the configured API base URL.
 */
export function getApiBaseUrl() {
    return API_BASE_URL;
}
