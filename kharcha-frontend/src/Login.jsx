import { useState } from "react";
import "./Login.css";
import { useNavigate } from "react-router-dom";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MOBILE_RE = /^[6-9]\d{9}$/;
const SPENDING = [
    { label: "Food", amount: 2180 },
    { label: "Travel", amount: 1420 },
    { label: "Study & other", amount: 1640 },
];
const BUDGET = 8000;
const SPENT = SPENDING.reduce((sum, item) => sum + item.amount, 0);

const inr = (n) => "₹" + n.toLocaleString("en-IN");

function validate({ identifier, password }) {
    const errors = {};
    const id = identifier.trim();

    if (!id) {
        errors.identifier = "Enter your email or mobile number.";
    } else if (!EMAIL_RE.test(id) && !MOBILE_RE.test(id.replace(/\s/g, ""))) {
        errors.identifier = "Enter a valid email or 10-digit mobile number.";
    }

    if (!password) {
        errors.password = "Enter your password.";
    } else if (password.length < 8) {
        errors.password = "Password must be at least 8 characters.";
    }

    return errors;
}

function EyeIcon({ off }) {
    return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
                d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinejoin="round"
            />
            <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8" />
            {off && (
                <path d="M4 4l16 16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            )}
        </svg>
    );
}

function GoogleIcon() {
    return (
        <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
            <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.9 2.4 30.4 0 24 0 14.6 0 6.5 5.4 2.6 13.2l7.9 6.1C12.4 13.6 17.7 9.5 24 9.5z" />
            <path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.7c-.6 3-2.3 5.5-4.8 7.2l7.6 5.9c4.5-4.1 7-10.2 7-17.6z" />
            <path fill="#FBBC05" d="M10.5 28.7A14.5 14.5 0 0 1 9.5 24c0-1.6.3-3.2.8-4.7l-7.9-6.1A24 24 0 0 0 0 24c0 3.9.9 7.5 2.6 10.8l7.9-6.1z" />
            <path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.6-5.9c-2.1 1.4-4.9 2.3-8.3 2.3-6.3 0-11.6-4.1-13.5-9.8l-7.9 6.1C6.5 42.6 14.6 48 24 48z" />
        </svg>
    );
}

function Login() {

    const navigate = useNavigate();
    const [showPassword, setShowPassword] = useState(false);
    const [formData, setFormData] = useState({ identifier: "", password: "" });
    const [remember, setRemember] = useState(true);
    const [touched, setTouched] = useState({});
    const [submitting, setSubmitting] = useState(false);
    const [formError, setFormError] = useState("");

    const errors = validate(formData);

    const handleChange = (e) => {
        setFormError("");
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleBlur = (e) => {
        setTouched({ ...touched, [e.target.name]: true });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setTouched({ identifier: true, password: true });
        if (Object.keys(errors).length > 0) return;

        setSubmitting(true);
        setFormError("");
        try {
            // TODO: replace with your real login request
            await new Promise((resolve) => setTimeout(resolve, 900));
            navigate('/dashboard')
            console.log({ ...formData, remember });
        } catch {
            setFormError("We couldn't sign you in. Check your details and try again.");
        } finally {
            setSubmitting(false);
        }
    };

    const showError = (field) => touched[field] && errors[field];

    return (
        <main className="login-page">
            <div className="login-container">
                {/* ============ LEFT: PRODUCT PREVIEW ============ */}
                <aside className="login-info" aria-label="About StudentPay">
                    <div className="brand">
                        <span className="brand-icon" aria-hidden="true">₹</span>
                        <span>StudentPay</span>
                    </div>

                    <div className="info-content">
                        <h1>Know where your money goes.</h1>
                        <p>
                            Track expenses, set a monthly budget and pay with UPI, all in one place.
                        </p>
                    </div>

                    <div className="preview" role="img" aria-label={`Sample: ${inr(SPENT)} spent of ${inr(BUDGET)} monthly budget`}>
                        <div className="preview-top">
                            <span className="preview-title">This month</span>
                            <span className="preview-budget">of {inr(BUDGET)}</span>
                        </div>
                        <p className="preview-spent">{inr(SPENT)}</p>

                        <div className="meter">
                            <span style={{ "--w": `${(SPENT / BUDGET) * 100}%` }} />
                        </div>
                        <p className="preview-left">{inr(BUDGET - SPENT)} left to spend</p>

                        <ul className="preview-list">
                            {SPENDING.map((item, i) => (
                                <li key={item.label}>
                                    <span className={`dot dot-${i}`} />
                                    <span className="preview-label">{item.label}</span>
                                    <span className="preview-amount">{inr(item.amount)}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </aside>

                {/* ============ RIGHT: FORM ============ */}
                <section className="login-form-section">
                    <div className="mobile-brand">
                        <span className="brand-icon" aria-hidden="true">₹</span>
                        <span>StudentPay</span>
                    </div>

                    <header className="form-header">
                        <h2>Welcome back</h2>
                        <p>Sign in to see your spending.</p>
                    </header>

                    {formError && (
                        <div className="form-alert" role="alert">
                            {formError}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} noValidate>
                        <div className="form-group">
                            <label htmlFor="identifier">Email or mobile number</label>
                            <input
                                id="identifier"
                                type="text"
                                name="identifier"
                                inputMode="email"
                                autoComplete="username"
                                value={formData.identifier}
                                onChange={handleChange}
                                onBlur={handleBlur}
                                placeholder="you@example.com"
                                aria-invalid={Boolean(showError("identifier"))}
                                aria-describedby={showError("identifier") ? "identifier-error" : undefined}
                            />
                            {showError("identifier") && (
                                <p className="field-error" id="identifier-error">
                                    {errors.identifier}
                                </p>
                            )}
                        </div>

                        <div className="form-group">
                            <div className="password-label">
                                <label htmlFor="password">Password</label>
                                <button
                                    type="button"
                                    className="link-button"
                                    onClick={() => alert("Password reset is coming soon.")}
                                >
                                    Forgot password?
                                </button>
                            </div>

                            <div className="password-input">
                                <input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    name="password"
                                    autoComplete="current-password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    onBlur={handleBlur}
                                    placeholder="At least 8 characters"
                                    aria-invalid={Boolean(showError("password"))}
                                    aria-describedby={showError("password") ? "password-error" : undefined}
                                />
                                <button
                                    type="button"
                                    className="toggle-visibility"
                                    onClick={() => setShowPassword(!showPassword)}
                                    aria-label={showPassword ? "Hide password" : "Show password"}
                                    aria-pressed={showPassword}
                                >
                                    <EyeIcon off={showPassword} />
                                </button>
                            </div>
                            {showError("password") && (
                                <p className="field-error" id="password-error">
                                    {errors.password}
                                </p>
                            )}
                        </div>

                        <div className="remember">
                            <input
                                type="checkbox"
                                id="remember"
                                checked={remember}
                                onChange={(e) => setRemember(e.target.checked)}
                            />
                            <label htmlFor="remember">Keep me signed in on this device</label>
                        </div>

                        <button type="submit" className="login-button" disabled={submitting} onClick={()=>navigate('/dashboard')}>
                            {submitting ? (
                                <>
                                    <span className="spinner" aria-hidden="true" />
                                    Signing in…
                                </>
                            ) : (
                                "Sign in"
                            )}
                        </button>
                    </form>

                    <div className="divider" role="separator">
                        <span />
                        <p>or</p>
                        <span />
                    </div>

                    <button type="button" className="google-button">
                        <GoogleIcon />
                        Continue with Google
                    </button>

                    <p className="signup-text">
                        New to StudentPay?
                        <button type="button" className="link-button" onClick={() => navigate("/signup")}>
                            Create an account
                        </button>
                    </p>
                </section>
            </div>
        </main>
    );
}

export default Login;