import { useState } from "react";
import "./Login.css";   // shared tokens, layout, fields, buttons
import "./Signup.css";  // signup-only additions
import { useNavigate } from "react-router-dom";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MOBILE_RE = /^[6-9]\d{9}$/;

const STEPS = [
  { title: "Create your account", text: "Takes about a minute." },
  { title: "Link your UPI ID", text: "Pay and track from one place." },
  { title: "Set a monthly budget", text: "See what's left as you spend." },
];

const STRENGTH_LABELS = ["Too short", "Weak", "Fair", "Good", "Strong"];

function getStrength(pw) {
  if (!pw) return 0;
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[a-z]/i.test(pw) && /\d/.test(pw)) score++;
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw) || pw.length >= 12) score++;
  return score;
}

function validate({ name, email, mobile, password, terms }) {
  const errors = {};

  if (name.trim().length < 2) errors.name = "Enter your full name.";

  if (!email.trim()) errors.email = "Enter your email address.";
  else if (!EMAIL_RE.test(email.trim())) errors.email = "Enter a valid email address.";

  if (!mobile) errors.mobile = "Enter your mobile number.";
  else if (!MOBILE_RE.test(mobile)) errors.mobile = "Enter a valid 10-digit mobile number.";

  if (!password) errors.password = "Create a password.";
  else if (password.length < 8) errors.password = "Password must be at least 8 characters.";
  else if (!/[a-z]/i.test(password) || !/\d/.test(password))
    errors.password = "Include at least one letter and one number.";

  if (!terms) errors.terms = "Accept the terms to create your account.";

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
      {off && <path d="M4 4l16 16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />}
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

function Signup() {
    function onNavigateToLogin(){
        navigate("/")
    }
    const navigate = useNavigate()
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    mobile: "",
    password: "",
    terms: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [touched, setTouched] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const errors = validate(formData);
  const strength = getStrength(formData.password);
  const showError = (field) => touched[field] && errors[field];

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormError("");
    setFormData({
      ...formData,
      [name]:
        type === "checkbox"
          ? checked
          : name === "mobile"
          ? value.replace(/\D/g, "").slice(0, 10) // digits only, max 10
          : value,
    });
  };

  const handleBlur = (e) => {
    setTouched({ ...touched, [e.target.name]: true });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setTouched({ name: true, email: true, mobile: true, password: true, terms: true });

    const firstInvalid = Object.keys(errors)[0];
    if (firstInvalid) {
      document.getElementById(firstInvalid)?.focus();
      return;
    }

    setSubmitting(true);
    setFormError("");
    try {
      // TODO: replace with your real signup request
      await new Promise((resolve) => setTimeout(resolve, 1000));
      sessionStorage.setItem("student_finance_user", JSON.stringify({ name: formData.name.trim() }));
      navigate("/onboarding");
    } catch {
      setFormError("We couldn't create your account. Try again in a moment.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="login-page">
      <div className="login-container">
        {/* ============ LEFT: ONBOARDING STEPS ============ */}
        <aside className="login-info" aria-label="Getting started with StudentPay">
          <div className="brand">
            <span className="brand-icon" aria-hidden="true">₹</span>
            <span>StudentPay</span>
          </div>

          <div className="info-content">
            <h1>Set up in under a minute.</h1>
            <p>
              Create an account, link your UPI ID and start tracking every rupee you spend.
            </p>
          </div>

          <ol className="steps">
            {STEPS.map((step, i) => (
              <li key={step.title} className={i === 0 ? "step current" : "step"}>
                <span className="step-num" aria-hidden="true">{i + 1}</span>
                <div>
                  <p className="step-title">{step.title}</p>
                  <p className="step-text">{step.text}</p>
                </div>
              </li>
            ))}
          </ol>
        </aside>

        {/* ============ RIGHT: FORM ============ */}
        <section className="login-form-section signup-form-section">
          <div className="mobile-brand">
            <span className="brand-icon" aria-hidden="true">₹</span>
            <span>StudentPay</span>
          </div>

          <header className="form-header">
            <h2>Create your account</h2>
            <p>Start tracking your spending today.</p>
          </header>

          {formError && (
            <div className="form-alert" role="alert">
              {formError}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            {/* NAME */}
            <div className="form-group">
              <label htmlFor="name">Full name</label>
              <input
                id="name"
                name="name"
                type="text"
                autoComplete="name"
                value={formData.name}
                onChange={handleChange}
                onBlur={handleBlur}
                placeholder="Aarav Sharma"
                aria-invalid={Boolean(showError("name"))}
                aria-describedby={showError("name") ? "name-error" : undefined}
              />
              {showError("name") && (
                <p className="field-error" id="name-error">{errors.name}</p>
              )}
            </div>

            {/* EMAIL */}
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                value={formData.email}
                onChange={handleChange}
                onBlur={handleBlur}
                placeholder="you@example.com"
                aria-invalid={Boolean(showError("email"))}
                aria-describedby={showError("email") ? "email-error" : undefined}
              />
              {showError("email") && (
                <p className="field-error" id="email-error">{errors.email}</p>
              )}
            </div>

            {/* MOBILE */}
            <div className="form-group">
              <label htmlFor="mobile">Mobile number</label>
              <div className="prefix-input">
                <span className="prefix" aria-hidden="true">+91</span>
                <input
                  id="mobile"
                  name="mobile"
                  type="tel"
                  inputMode="numeric"
                  autoComplete="tel-national"
                  value={formData.mobile}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  placeholder="98765 43210"
                  aria-invalid={Boolean(showError("mobile"))}
                  aria-describedby={showError("mobile") ? "mobile-error" : undefined}
                />
              </div>
              {showError("mobile") && (
                <p className="field-error" id="mobile-error">{errors.mobile}</p>
              )}
            </div>

            {/* PASSWORD */}
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <div className="password-input">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  value={formData.password}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  placeholder="At least 8 characters"
                  aria-invalid={Boolean(showError("password"))}
                  aria-describedby="password-hint"
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

              <div className="strength" data-level={strength} aria-hidden="true">
                <span /><span /><span /><span />
              </div>
              <p className="hint" id="password-hint">
                {formData.password
                  ? `Password strength: ${STRENGTH_LABELS[strength]}`
                  : "Use 8+ characters with letters and numbers."}
              </p>
              {showError("password") && (
                <p className="field-error" role="alert">{errors.password}</p>
              )}
            </div>

            {/* TERMS */}
            <div className="terms">
              <div className="terms-row">
                <input
                  type="checkbox"
                  id="terms"
                  name="terms"
                  checked={formData.terms}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  aria-invalid={Boolean(showError("terms"))}
                />
                <label htmlFor="terms">
                  I agree to the <a href="/terms">Terms of Service</a> and{" "}
                  <a href="/privacy">Privacy Policy</a>.
                </label>
              </div>
              {showError("terms") && (
                <p className="field-error">{errors.terms}</p>
              )}
            </div>

            <button type="submit" className="login-button" disabled={submitting}>
              {submitting ? (
                <>
                  <span className="spinner" aria-hidden="true" />
                  Creating account…
                </>
              ) : (
                "Create account"
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
            Sign up with Google
          </button>

          <p className="signup-text">
            Already have an account?
            <button type="button" className="link-button" onClick={onNavigateToLogin}>
              Sign in
            </button>
          </p>
        </section>
      </div>
    </main>
  );
}

export default Signup;
