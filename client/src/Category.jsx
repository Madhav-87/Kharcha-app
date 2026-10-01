import { useState } from "react";
import {
  Plus,
  Utensils,
  Bus,
  GraduationCap,
  ShoppingBag,
  Gamepad2,
  Lightbulb,
  Home,
  HeartPulse,
  Smartphone,
  MoreHorizontal,
  Pencil,
  Trash2,
} from "lucide-react";
import AddCategory from "./AddCategory";
import Sidebar from "./Sidebar";
import "./Category.css";

const initialCategoriesData = [
  {
    id: 1,
    name: "Food",
    icon: Utensils,
    bg: "#e0e7ff",
    color: "#4338ca",
    isDefault: true,
  },
  {
    id: 2,
    name: "Transport",
    icon: Bus,
    bg: "#f3e8ff",
    color: "#7e22ce",
    isDefault: true,
  },
  {
    id: 3,
    name: "Education",
    icon: GraduationCap,
    bg: "#dbeafe",
    color: "#1d4ed8",
    isDefault: true,
  },
  {
    id: 4,
    name: "Shopping",
    icon: ShoppingBag,
    bg: "#fce7f3",
    color: "#be185d",
    isDefault: true,
  },
  {
    id: 5,
    name: "Entertainment",
    icon: Gamepad2,
    bg: "#ffedd5",
    color: "#ea580c",
    isDefault: true,
  },
  {
    id: 6,
    name: "Bills",
    icon: Lightbulb,
    bg: "#fef9c3",
    color: "#ca8a04",
    isDefault: true,
  },
  {
    id: 7,
    name: "Hostel/Rent",
    icon: Home,
    bg: "#d1fae5",
    color: "#047857",
    isDefault: true,
  },
  {
    id: 8,
    name: "Healthcare",
    icon: HeartPulse,
    bg: "#ffe4e6",
    color: "#e11d48",
    isDefault: true,
  },
  {
    id: 9,
    name: "Recharge",
    icon: Smartphone,
    bg: "#e0f2fe",
    color: "#0369a1",
    isDefault: true,
  },
  {
    id: 10,
    name: "Other",
    icon: MoreHorizontal,
    bg: "#f1f5f9",
    color: "#475569",
    isDefault: true,
  },
];

function Category() {
  const [categories, setCategories] = useState(initialCategoriesData);
  const [isAddCategoryOpen, setIsAddCategoryOpen] = useState(false);

  const handleAddCategory = (newCategory) => {
    setCategories((currentCategories) => [
      ...currentCategories,
      { ...newCategory, id: Date.now(), isDefault: false },
    ]);
  };

  const handleEdit = (category) => {
    console.log("Edit:", category.name);
  };

  const handleDelete = (category) => {
    setCategories((currentCategories) =>
      currentCategories.filter((currentCategory) => currentCategory.id !== category.id),
    );
  };

  return (
    <div className="app-container category-app-container">
      <Sidebar activePage="categories" />

      <main className="main-content">
        <div className="dashboard-max-width">
          <section className="categories-page">
            <header className="categories-header">
              <div>
                <p className="categories-subtitle">Customize your tracking</p>
                <h1 className="categories-title">Categories</h1>
              </div>

              <button
                className="add-category-btn"
                onClick={() => setIsAddCategoryOpen(true)}
              >
                <Plus size={18} />
                Add Category
              </button>
            </header>

            <div className="category-grid">
              {categories.map((category) => {
                const Icon = category.icon;

                return (
                  <article key={category.id} className="category-card">
                    <div className="category-actions">
                      <button
                        className="action-btn"
                        title="Edit category"
                        aria-label={`Edit ${category.name} category`}
                        onClick={() => handleEdit(category)}
                      >
                        <Pencil size={16} />
                      </button>
                      <button
                        className="action-btn delete"
                        title="Delete category"
                        aria-label={`Delete ${category.name} category`}
                        onClick={() => handleDelete(category)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>

                    <div
                      className="category-icon"
                      style={{ backgroundColor: category.bg, color: category.color }}
                    >
                      <Icon size={26} />
                    </div>
                    <h2 className="category-name">{category.name}</h2>
                    <span className="category-type">
                      {category.isDefault ? "Default" : "Custom"}
                    </span>
                  </article>
                );
              })}
            </div>
          </section>
        </div>
      </main>

      {isAddCategoryOpen && (
        <AddCategory
          onAdd={handleAddCategory}
          onClose={() => setIsAddCategoryOpen(false)}
        />
      )}
    </div>
  );
}

export default Category;