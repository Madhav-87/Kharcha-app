import { useEffect, useState } from "react";
import {
  Book,
  Bus,
  Camera,
  Car,
  Check,
  Coffee,
  Dumbbell,
  Film,
  Gift,
  Gamepad2,
  HeartPulse,
  Home,
  Lightbulb,
  MoreHorizontal,
  Music,
  Pill,
  Plane,
  Scissors,
  Shirt,
  ShoppingBag,
  Smartphone,
  Train,
  Tv,
  Utensils,
  X,
  Zap,
  GraduationCap,
} from "lucide-react";
import "./AddCategory.css";

const AVAILABLE_ICONS = {
  Utensils,
  Bus,
  Tv,
  Home,
  ShoppingBag,
  Smartphone,
  Train,
  GraduationCap,
  Gamepad2,
  Lightbulb,
  HeartPulse,
  MoreHorizontal,
  Coffee,
  Plane,
  Shirt,
  Film,
  Zap,
  Pill,
  Gift,
  Music,
  Dumbbell,
  Car,
  Scissors,
  Book,
  Camera,
};

const COLOR_THEMES = [
  { bg: "#e0e7ff", color: "#4338ca", name: "Indigo" },
  { bg: "#d1fae5", color: "#047857", name: "Emerald" },
  { bg: "#fef9c3", color: "#ca8a04", name: "Amber" },
  { bg: "#ffe4e6", color: "#e11d48", name: "Rose" },
  { bg: "#f3e8ff", color: "#7e22ce", name: "Purple" },
  { bg: "#e0f2fe", color: "#0369a1", name: "Sky" },
  { bg: "#ffedd5", color: "#ea580c", name: "Orange" },
  { bg: "#f1f5f9", color: "#475569", name: "Slate" },
];

function AddCategory({ onAdd, onClose }) {
  const [name, setName] = useState("");
  const [iconKey, setIconKey] = useState("Coffee");
  const [colorIndex, setColorIndex] = useState(0);

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  function handleSubmit(event) {
    event.preventDefault();

    const trimmedName = name.trim();
    if (!trimmedName) return;

    const selectedTheme = COLOR_THEMES[colorIndex];
    onAdd({
      name: trimmedName,
      icon: AVAILABLE_ICONS[iconKey],
      bg: selectedTheme.bg,
      color: selectedTheme.color,
    });
    onClose();
  }

  return (
    <div className="add-category-overlay" onClick={onClose}>
      <section
        className="add-category-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="add-category-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="add-category-header">
          <div>
            <p className="add-category-eyebrow">Personalize your budget</p>
            <h2 id="add-category-title">Add category</h2>
          </div>
          <button
            className="add-category-close"
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
          >
            <X size={19} />
          </button>
        </header>

        <form onSubmit={handleSubmit}>
          <div className="add-category-body">
            <div className="add-category-field">
              <label htmlFor="category-name">Category name</label>
              <input
                id="category-name"
                autoFocus
                autoComplete="off"
                maxLength={32}
                placeholder="e.g. Groceries, Gym, Books"
                value={name}
                onChange={(event) => setName(event.target.value)}
                required
              />
            </div>

            <fieldset className="add-category-field">
              <legend>Choose an icon</legend>
              <div className="category-icon-options">
                {Object.entries(AVAILABLE_ICONS).map(([key, Icon]) => (
                  <button
                    key={key}
                    className={`category-icon-option ${iconKey === key ? "selected" : ""}`}
                    type="button"
                    title={key}
                    aria-label={`${key} icon`}
                    aria-pressed={iconKey === key}
                    onClick={() => setIconKey(key)}
                  >
                    <Icon size={19} />
                  </button>
                ))}
              </div>
            </fieldset>

            <fieldset className="add-category-field">
              <legend>Choose a color</legend>
              <div className="category-color-options">
                {COLOR_THEMES.map((theme, index) => (
                  <button
                    key={theme.name}
                    className={`category-color-option ${colorIndex === index ? "selected" : ""}`}
                    type="button"
                    title={theme.name}
                    aria-label={`${theme.name} color`}
                    aria-pressed={colorIndex === index}
                    style={{ backgroundColor: theme.bg, color: theme.color }}
                    onClick={() => setColorIndex(index)}
                  >
                    {colorIndex === index && <Check size={17} />}
                  </button>
                ))}
              </div>
            </fieldset>
          </div>

          <footer className="add-category-footer">
            <button className="add-category-cancel" type="button" onClick={onClose}>
              Cancel
            </button>
            <button className="add-category-save" type="submit" disabled={!name.trim()}>
              Add category
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

export default AddCategory;