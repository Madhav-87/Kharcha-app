import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Bus,
  Check,
  Clapperboard,
  HeartPulse,
  Home,
  IndianRupee,
  Lightbulb,
  MoreHorizontal,
  ShoppingBag,
  Smartphone,
  Utensils,
} from "lucide-react";
import "./Onboarding.css";

// Each number represents one screen in the onboarding flow.
const PROFILE_STEP = 0;
const UPI_STEP = 1;
const CATEGORIES_STEP = 2;
const COMPLETE_STEP = 3;
const TOTAL_STEPS = 4;

const UPI_ID_PATTERN = /^[a-zA-Z0-9._-]{2,256}@[a-zA-Z][a-zA-Z0-9.-]{1,63}$/;
const DEFAULT_CATEGORIES = ["Food", "Transport", "Education"];

// These are the same default categories used by the app.
const CATEGORIES = [
  { id: "Food", Icon: Utensils },
  { id: "Transport", Icon: Bus },
  { id: "Education", Icon: BookOpen },
  { id: "Shopping", Icon: ShoppingBag },
  { id: "Entertainment", Icon: Clapperboard },
  { id: "Bills", Icon: Lightbulb },
  { id: "Hostel/Rent", label: "Hostel / Rent", Icon: Home },
  { id: "Healthcare", Icon: HeartPulse },
  { id: "Recharge", Icon: Smartphone },
  { id: "Other", Icon: MoreHorizontal },
];

// Safely read a saved object from browser storage.
function readSavedProfile() {
  try {
    return JSON.parse(localStorage.getItem("student_finance_onboarding") || "{}");
  } catch {
    return {};
  }
}

function readSignupUser() {
  try {
    return JSON.parse(sessionStorage.getItem("student_finance_user") || "{}");
  } catch {
    return {};
  }
}

function getStartingCategories() {
  const savedCategories = readSavedProfile().categories;

  if (!Array.isArray(savedCategories)) {
    return DEFAULT_CATEGORIES;
  }

  // Match saved names to the current category list, ignoring capitalization.
  const validCategories = [];
  for (const savedName of savedCategories) {
    const matchingCategory = CATEGORIES.find(
      (category) => category.id.toLowerCase() === String(savedName).toLowerCase(),
    );

    if (matchingCategory) {
      validCategories.push(matchingCategory.id);
    }
  }

  return validCategories.length > 0 ? validCategories : DEFAULT_CATEGORIES;
}

function BirdCompanion({ step }) {
  return (
    <div className={`bird-scene bird-scene-${step}`} aria-label="A small animated blue bird accompanies your setup">
      <div className="bird-soft-shadow" />
      <div className="bird-flight-line" />

      <svg className="bird-illustration" viewBox="0 0 230 190" role="img" aria-label="Blue bird in flight">
        <g className="bird-tail"><path d="M61 105 35 89l10 28-17 9 35 1z" /></g>
        <g className="bird-wing"><path d="M94 87c-13-17-30-24-47-19 7 10 14 18 24 25-13-3-25 0-35 8 17 11 39 13 59 4z" /></g>
        <path className="bird-body" d="M66 102c3-27 24-47 51-48 28-1 50 17 54 43 3 25-14 46-39 51-27 5-58-10-66-34-1-4-1-8 0-12z" />
        <path className="bird-belly" d="M93 117c4-13 15-22 29-22 18 0 29 13 28 28-1 12-11 20-25 22-15 1-30-9-32-21z" />
        <path className="bird-beak" d="m165 85 31 8-29 8z" />
        <circle className="bird-eye" cx="151" cy="78" r="3.5" />
        <path className="bird-brow" d="M146 70c4-3 9-3 13-1" />
        <path className="bird-feet" d="m112 145-2 10m12-11 1 10m-17 0-7 3m7-3 6 3m5-3 7 3m-7-3 1-4" />
        <path className="bird-wing-mark" d="M90 94c9-9 21-12 32-8" />
      </svg>

      {/* The same bird gets a different prop for each question. */}
      {step === PROFILE_STEP && (
        <div className="bird-note welcome-note">
          <span>Hello!</span>
          <small>Nice to meet you.</small>
        </div>
      )}
      {step === UPI_STEP && (
        <div className="bird-note payment-note">
          <span className="payment-note-icon"><IndianRupee size={15} /></span>
          <span>UPI details</span>
          <Check size={13} className="payment-note-check" />
        </div>
      )}
      {step === CATEGORIES_STEP && (
        <div className="bird-category-notes">
          <span><Utensils size={13} /></span>
          <span><BookOpen size={13} /></span>
          <span><Bus size={13} /></span>
        </div>
      )}
      {step === COMPLETE_STEP && (
        <div className="bird-ready-note">
          <Check size={14} />
          <span>Ready to go</span>
        </div>
      )}

      <span className="bird-caption">Your little money companion</span>
    </div>
  );
}

function Onboarding() {
  const navigate = useNavigate();

  // Each answer has its own state variable, which makes it easy to follow.
  const [name, setName] = useState(() => {
    const signupUser = readSignupUser();
    const savedProfile = readSavedProfile();
    return signupUser.name || savedProfile.name || "";
  });
  const [upiId, setUpiId] = useState(() => readSavedProfile().upiId || "");
  const [categories, setCategories] = useState(getStartingCategories);

  const [step, setStep] = useState(PROFILE_STEP);
  const [nameError, setNameError] = useState("");
  const [categoryError, setCategoryError] = useState("");
  const [upiTouched, setUpiTouched] = useState(false);

  const isUpiValid = UPI_ID_PATTERN.test(upiId.trim());
  const showUpiError = upiTouched && !isUpiValid;

  function toggleCategory(categoryId) {
    const alreadySelected = categories.includes(categoryId);

    if (alreadySelected) {
      setCategories(categories.filter((category) => category !== categoryId));
    } else {
      setCategories([...categories, categoryId]);
    }

    setCategoryError("");
  }

  function handleContinue() {
    if (step === PROFILE_STEP) {
      if (!name.trim()) {
        setNameError("Enter your name to continue.");
        document.getElementById("onboarding-name")?.focus();
        return;
      }

      setNameError("");
      setStep(UPI_STEP);
      return;
    }

    if (step === UPI_STEP) {
      setUpiTouched(true);

      if (!isUpiValid) {
        document.getElementById("onboarding-upi")?.focus();
        return;
      }

      setStep(CATEGORIES_STEP);
      return;
    }

    if (step === CATEGORIES_STEP) {
      if (categories.length === 0) {
        setCategoryError("Choose at least one category.");
        return;
      }

      setCategoryError("");
      setStep(COMPLETE_STEP);
    }
  }

  function handleBack() {
    setStep(step - 1);
  }

  function finishOnboarding() {
    const profile = {
      name: name.trim(),
      upiId: upiId.trim(),
      categories,
      completed: true,
      completedAt: new Date().toISOString(),
    };

    localStorage.setItem("student_finance_onboarding", JSON.stringify(profile));
    navigate("/dashboard", { replace: true });
  }

  function renderQuestion() {
    if (step === PROFILE_STEP) {
      return (
        <>
          <span className="question-eyebrow">YOUR PROFILE</span>
          <h1>What should we call you?</h1>
          <p className="question-description">Tell us your name so we can make your Kharcha experience feel a little more personal.</p>

          <div className="onboarding-field">
            <label htmlFor="onboarding-name">Your name</label>
            <input
              id="onboarding-name"
              type="text"
              autoComplete="name"
              placeholder="Enter your name"
              value={name}
              onChange={(event) => {
                setName(event.target.value);
                setNameError("");
              }}
              aria-invalid={Boolean(nameError)}
              aria-describedby={nameError ? "name-error" : undefined}
            />
            {nameError && <p className="onboarding-error" id="name-error" role="alert">{nameError}</p>}
          </div>
        </>
      );
    }

    if (step === UPI_STEP) {
      return (
        <>
          <span className="question-eyebrow">PAYMENT DETAILS</span>
          <h1>What's your UPI ID?</h1>
          <p className="question-description">Add your UPI ID so Kharcha can make your payment experience easier.</p>

          <div className="onboarding-field">
            <label htmlFor="onboarding-upi">UPI ID</label>
            <input
              id="onboarding-upi"
              type="text"
              autoComplete="off"
              spellCheck="false"
              placeholder="example@upi"
              value={upiId}
              onChange={(event) => {
                setUpiId(event.target.value);
                setUpiTouched(true);
              }}
              onBlur={() => setUpiTouched(true)}
              aria-invalid={showUpiError}
              aria-describedby={showUpiError ? "upi-error" : upiTouched && isUpiValid ? "upi-valid" : "upi-hint"}
            />
            {showUpiError ? (
              <p className="onboarding-error" id="upi-error" role="alert">Enter a valid UPI ID.</p>
            ) : upiTouched && isUpiValid ? (
              <p className="onboarding-valid" id="upi-valid"><Check size={14} /> Looks good</p>
            ) : (
              <p className="onboarding-helper" id="upi-hint">You can update this later from your payment settings.</p>
            )}
          </div>

          <p className="upi-privacy-note">Kharcha will never ask for your UPI PIN or OTP.</p>
        </>
      );
    }

    if (step === CATEGORIES_STEP) {
      return (
        <>
          <span className="question-eyebrow">YOUR SPENDING</span>
          <h1>What do you usually spend on?</h1>
          <p className="question-description">Choose the categories you use most. You can always change them later.</p>

          <div className="onboarding-category-grid" aria-label="Spending categories">
            {CATEGORIES.map((category) => {
              const CategoryIcon = category.Icon;
              const isSelected = categories.includes(category.id);

              return (
                <button
                  type="button"
                  className={`onboarding-category ${isSelected ? "selected" : ""}`}
                  key={category.id}
                  aria-pressed={isSelected}
                  onClick={() => toggleCategory(category.id)}
                >
                  <CategoryIcon size={17} strokeWidth={1.8} />
                  <span>{category.label || category.id}</span>
                  <span className="category-selected-check">{isSelected && <Check size={12} />}</span>
                </button>
              );
            })}
          </div>

          {categoryError && <p className="onboarding-error" role="alert">{categoryError}</p>}
        </>
      );
    }

    return (
      <>
        <span className="completion-check"><Check size={23} /></span>
        <span className="question-eyebrow">PROFILE COMPLETE</span>
        <h1>You're all set!</h1>
        <p className="question-description">Your Kharcha profile is ready. Let's take you to your dashboard.</p>

        <div className="completion-summary">
          <span>Ready for you,</span>
          <strong>{name.trim() || "Student"}</strong>
          <small>{categories.length} spending {categories.length === 1 ? "category" : "categories"} selected</small>
        </div>
      </>
    );
  }

  return (
    <main className="kh-onboarding">
      <div className="kh-onboarding-shell">
        <header className="kh-header">
          <button type="button" className="kh-wordmark" onClick={() => navigate("/")} aria-label="Kharcha home">
            <span className="kh-mark">K</span>
            <span>kharcha</span>
          </button>
          <div className="kh-signin-prompt">
            Already have an account?
            <button type="button" onClick={() => navigate("/")}>Sign in</button>
          </div>
        </header>

        <section className="onboarding-card" aria-label="Kharcha account setup">
          <div className="onboarding-visual">
            <BirdCompanion step={step} />
          </div>

          <div className="onboarding-form-panel">
            <div className="onboarding-progress">
              <span>0{step + 1} <i>/ 0{TOTAL_STEPS}</i></span>
              <div
                className="onboarding-progress-track"
                role="progressbar"
                aria-label="Onboarding progress"
                aria-valuemin="1"
                aria-valuemax={TOTAL_STEPS}
                aria-valuenow={step + 1}
              >
                <span style={{ width: `${((step + 1) / TOTAL_STEPS) * 100}%` }} />
              </div>
            </div>

            <div className="onboarding-question" key={step}>
              {renderQuestion()}
            </div>

            <div className="onboarding-actions">
              {step > PROFILE_STEP && step < COMPLETE_STEP && (
                <button type="button" className="onboarding-back" onClick={handleBack}>
                  <ArrowLeft size={16} /> Back
                </button>
              )}

              {step < COMPLETE_STEP ? (
                <button type="button" className="onboarding-continue" onClick={handleContinue}>
                  Continue <ArrowRight size={16} />
                </button>
              ) : (
                <button type="button" className="onboarding-continue" onClick={finishOnboarding}>
                  Go to Dashboard <ArrowRight size={16} />
                </button>
              )}
            </div>
          </div>
        </section>

        <p className="onboarding-footer-note">A simple way to stay in control of your student spending.</p>
      </div>
    </main>
  );
}

export default Onboarding;
