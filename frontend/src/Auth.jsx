
import { useState } from "react";
import "./Auth.css";

const API_URL = "http://127.0.0.1:8000";

export default function Auth({ onLogin }) {
    const [isRegister, setIsRegister] = useState(false);
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");

    async function handleSubmit(event) {
        event.preventDefault();
        setLoading(true);
        setMessage("");
        setError("");

        const endpoint = isRegister ? "/auth/register" : "/auth/login";

        const body = isRegister
            ? { name, email, password }
            : { email, password };

        try {
            const response = await fetch(`${API_URL}${endpoint}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(body),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    typeof data.detail === "string"
                        ? data.detail
                        : "Please check your details and try again."
                );
            }

            if (isRegister) {
                setMessage("Registration successful! You can now log in.");
                setIsRegister(false);
                setPassword("");
            } else {
                onLogin(data);
            }
        } catch (err) {
            setError(err.message || "Unable to connect to the server.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="auth-page">
            <div className="auth-card">
                <div className="auth-brand">AI Media Integrity Detector</div>

                <h1>{isRegister ? "Create Account" : "Welcome Back"}</h1>

                <p className="auth-subtitle">
                    {isRegister
                        ? "Register to analyze and review digital media."
                        : "Log in to access your media analysis dashboard."}
                </p>

                {message && <div className="auth-message">{message}</div>}
                {error && <div className="auth-error">{error}</div>}

                <form onSubmit={handleSubmit}>
                    {isRegister && (
                        <div className="auth-field">
                            <label htmlFor="auth-name">Full Name</label>
                            <input
                                id="auth-name"
                                type="text"
                                placeholder="Enter your name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                maxLength={100}
                                required
                            />
                        </div>
                    )}

                    <div className="auth-field">
                        <label htmlFor="auth-email">Email Address</label>
                        <input
                            id="auth-email"
                            type="email"
                            placeholder="Enter your email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            autoComplete="email"
                            required
                        />
                    </div>

                    <div className="auth-field">
                        <label htmlFor="auth-password">Password</label>
                        <input
                            id="auth-password"
                            type="password"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            autoComplete={isRegister ? "new-password" : "current-password"}
                            minLength={isRegister ? 8 : undefined}
                            required
                        />
                    </div>

                    <button
                        className="auth-submit"
                        type="submit"
                        disabled={loading}
                    >
                        {loading
                            ? "Please wait..."
                            : isRegister
                                ? "Create Account"
                                : "Login"}
                    </button>
                </form>

                <p className="auth-switch">
                    {isRegister
                        ? "Already have an account?"
                        : "Don't have an account?"}{" "}
                    <button
                        type="button"
                        onClick={() => {
                            setIsRegister(!isRegister);
                            setMessage("");
                            setError("");
                        }}
                    >
                        {isRegister ? "Login" : "Register"}
                    </button>
                </p>
            </div>
        </div>
    );
}
