import {
  ArrowUpRight,
  BarChart2,
  LayoutDashboard,
  PieChart,
  ReceiptText,
  Shapes,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import "./Dashboard.css";
import "./Sidebar.css";

const navigationItems = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/dashboard", page: "dashboard" },
  { label: "Transactions", icon: ReceiptText, path: "/transactions", page: "transactions" },
  { label: "Budgets", icon: PieChart, path: "#", page: "budgets" },
  { label: "UPI Pay", icon: ArrowUpRight, path: "#", page: "pay" },
  { label: "Insights", icon: BarChart2, path: "#", page: "insights" },
  { label: "Categories", icon: Shapes, path: "/category", page: "categories" },
];

function Sidebar({ activePage }) {
  const navigate = useNavigate();

  return (
    <aside className="sidebar">
      <div>
        <div className="sidebar-logo">
          <div className="logo-circle">P</div>
          <div>
            <h1>Paisa</h1>
            <p>Student finance</p>
          </div>
        </div>

        <nav className="sidebar-nav" aria-label="Main navigation">
          {navigationItems.map(({ label, icon: Icon, path, page }) => {
            const isActive = activePage === page;

            return (
              <button
                key={page}
                className={`nav-item ${isActive ? "active" : ""}`}
                onClick={() => navigate(path)}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon size={20} />
                <span>{label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="monthly-goal">
        <p className="goal-title">Monthly Goal</p>
        <h3 className="goal-amount">Save ₹3,000</h3>
        <div className="goal-track">
          <div className="goal-fill" />
        </div>
        <p className="goal-desc">₹2,000 of ₹3,000 saved</p>
      </div>
    </aside>
  );
}

export default Sidebar;