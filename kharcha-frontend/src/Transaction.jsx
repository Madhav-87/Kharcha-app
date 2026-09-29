import { useState } from "react";
import {
  AlertCircle,
  ArrowDownLeft,
  Bus,
  CheckCircle2,
  Clock,
  Download,
  GraduationCap,
  Search,
  Smartphone,
  Train,
  Tv,
  Utensils,
} from "lucide-react";
import Sidebar from "./Sidebar";
import "./Transaction.css";

const transactions = [
  {
    id: 1,
    title: "Campus Canteen",
    category: "Food",
    time: "Today · 12:45 PM",
    amount: "-₹180",
    isPositive: false,
    status: "Paid",
    method: "UPI",
    icon: Utensils,
    iconColor: "#4338ca",
    iconBg: "#e0e7ff",
  },
  {
    id: 2,
    title: "Uber Rides",
    category: "Transport",
    time: "Today · 10:20 AM",
    amount: "-₹240",
    isPositive: false,
    status: "Paid",
    method: "UPI",
    icon: Bus,
    iconColor: "#7e22ce",
    iconBg: "#f3e8ff",
  },
  {
    id: 3,
    title: "Dad",
    category: "Allowance",
    time: "Yesterday · 09:00 AM",
    amount: "+₹5,000",
    isPositive: true,
    status: "Paid",
    method: "Bank Transfer",
    icon: ArrowDownLeft,
    iconColor: "#047857",
    iconBg: "#d1fae5",
  },
  {
    id: 4,
    title: "Netflix Subscription",
    category: "Entertainment",
    time: "27 Sep · 08:00 AM",
    amount: "-₹199",
    isPositive: false,
    status: "Pending",
    method: "Card",
    icon: Tv,
    iconColor: "#ea580c",
    iconBg: "#ffedd5",
  },
  {
    id: 5,
    title: "Jio Recharge",
    category: "Bills",
    time: "26 Sep · 02:15 PM",
    amount: "-₹299",
    isPositive: false,
    status: "Failed",
    method: "UPI",
    icon: Smartphone,
    iconColor: "#e11d48",
    iconBg: "#ffe4e6",
  },
  {
    id: 6,
    title: "College Books",
    category: "Education",
    time: "25 Sep · 11:30 AM",
    amount: "-₹850",
    isPositive: false,
    status: "Paid",
    method: "UPI",
    icon: GraduationCap,
    iconColor: "#0369a1",
    iconBg: "#e0f2fe",
  },
  {
    id: 7,
    title: "Metro Card Top-up",
    category: "Transport",
    time: "22 Sep · 09:10 AM",
    amount: "-₹300",
    isPositive: false,
    status: "Paid",
    method: "UPI",
    icon: Train,
    iconColor: "#475569",
    iconBg: "#f1f5f9",
  },
];

const statusFilters = ["All", "Paid", "Pending", "Failed"];
const categoryFilters = ["All categories", ...new Set(transactions.map(({ category }) => category))];
const statusIcons = {
  Paid: CheckCircle2,
  Pending: Clock,
  Failed: AlertCircle,
};

function escapeCsv(value) {
  return `"${String(value).replace(/"/g, '""')}"`;
}

function Transaction() {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeStatus, setActiveStatus] = useState("All");
  const [activeCategory, setActiveCategory] = useState("All categories");

  const visibleTransactions = transactions.filter((transaction) => {
    const searchText = `${transaction.title} ${transaction.category} ${transaction.method}`.toLowerCase();
    const matchesSearch = searchText.includes(searchQuery.trim().toLowerCase());
    const matchesStatus = activeStatus === "All" || transaction.status === activeStatus;
    const matchesCategory =
      activeCategory === "All categories" || transaction.category === activeCategory;

    return matchesSearch && matchesStatus && matchesCategory;
  });

  function exportTransactions() {
    const columns = ["Description", "Category", "Date", "Method", "Status", "Amount"];
    const rows = visibleTransactions.map((transaction) => [
      transaction.title,
      transaction.category,
      transaction.time,
      transaction.method,
      transaction.status,
      transaction.amount,
    ]);
    const csv = [columns, ...rows].map((row) => row.map(escapeCsv).join(",")).join("\n");
    const downloadUrl = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");

    link.href = downloadUrl;
    link.download = "transactions.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(downloadUrl);
  }

  return (
    <div className="app-container transactions-app-container">
      <Sidebar activePage="transactions" />

      <main className="main-content">
        <div className="dashboard-max-width">
          <section className="transactions-page">
            <header className="transactions-header">
              <div>
                <p className="transactions-eyebrow">Activity</p>
                <h1 className="transactions-title">Transactions</h1>
              </div>
              <button
                className="transactions-export"
                type="button"
                onClick={exportTransactions}
                disabled={visibleTransactions.length === 0}
              >
                <Download size={17} />
                <span>Export CSV</span>
              </button>
            </header>

            <div className="transactions-controls">
              <label className="transactions-search">
                <Search size={18} aria-hidden="true" />
                <span className="visually-hidden">Search transactions</span>
                <input
                  type="search"
                  placeholder="Search transactions..."
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                />
              </label>

              <label className="transactions-category-filter">
                <span className="visually-hidden">Filter by category</span>
                <select
                  value={activeCategory}
                  onChange={(event) => setActiveCategory(event.target.value)}
                >
                  {categoryFilters.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="transactions-tabs" role="group" aria-label="Filter by status">
              {statusFilters.map((status) => {
                const count =
                  status === "All"
                    ? transactions.length
                    : transactions.filter((transaction) => transaction.status === status).length;

                return (
                  <button
                    key={status}
                    className={`transactions-tab ${activeStatus === status ? "active" : ""}`}
                    type="button"
                    aria-pressed={activeStatus === status}
                    onClick={() => setActiveStatus(status)}
                  >
                    <span>{status}</span>
                    <span className="transactions-tab-count">{count}</span>
                  </button>
                );
              })}
            </div>

            <div className="transactions-table-wrap">
              <table className="transactions-table">
                <thead>
                  <tr>
                    <th scope="col">Transaction</th>
                    <th scope="col" className="transaction-category-column">Category</th>
                    <th scope="col" className="transaction-method-column">Method</th>
                    <th scope="col">Status</th>
                    <th scope="col" className="transaction-amount-heading">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleTransactions.map((transaction) => {
                    const Icon = transaction.icon;
                    const StatusIcon = statusIcons[transaction.status];

                    return (
                      <tr key={transaction.id}>
                        <td>
                          <div className="transaction-description">
                            <span
                              className="transaction-icon"
                              style={{
                                backgroundColor: transaction.iconBg,
                                color: transaction.iconColor,
                              }}
                            >
                              <Icon size={19} />
                            </span>
                            <span className="transaction-description-text">
                              <span className="transaction-name">{transaction.title}</span>
                              <span className="transaction-time">{transaction.time}</span>
                              <span className="transaction-mobile-category">
                                {transaction.category}
                              </span>
                            </span>
                          </div>
                        </td>
                        <td className="transaction-category-column">{transaction.category}</td>
                        <td className="transaction-method-column">{transaction.method}</td>
                        <td>
                          <span className={`transaction-status status-${transaction.status.toLowerCase()}`}>
                            <StatusIcon size={14} />
                            {transaction.status}
                          </span>
                        </td>
                        <td className={`transaction-amount ${transaction.isPositive ? "positive" : ""}`}>
                          {transaction.amount}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {visibleTransactions.length === 0 && (
                <div className="transactions-empty-state">
                  <Search size={25} />
                  <h2>No transactions found</h2>
                  <p>Try changing your search or filters.</p>
                  <button
                    type="button"
                    onClick={() => {
                      setSearchQuery("");
                      setActiveStatus("All");
                      setActiveCategory("All categories");
                    }}
                  >
                    Clear filters
                  </button>
                </div>
              )}
            </div>

            <p className="transactions-result-count" aria-live="polite">
              Showing {visibleTransactions.length} of {transactions.length} transactions
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}

export default Transaction;