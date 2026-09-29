import { useMemo, useState } from 'react'
import {
  ArrowDownLeft,
  ArrowUpRight,
  PiggyBank,
  TrendingUp,
  Wallet,
} from 'lucide-react'
import Sidebar from './Sidebar'
import './Insight.css'

const overviewStats = [
  {
    title: 'Income',
    value: '₹24,500',
    change: '+8.2%',
    icon: ArrowDownLeft,
    accent: '#10b981',
    bg: '#dcfce7',
  },
  {
    title: 'Expenses',
    value: '₹16,820',
    change: '-4.1%',
    icon: ArrowUpRight,
    accent: '#ef4444',
    bg: '#fee2e2',
  },
  {
    title: 'Savings',
    value: '₹7,680',
    change: '+12.4%',
    icon: PiggyBank,
    accent: '#4f46e5',
    bg: '#e0e7ff',
  },
]

const categoryData = [
  { name: 'Food', spent: 4200, budget: 5000, color: '#4f46e5' },
  { name: 'Rent', spent: 2600, budget: 2800, color: '#10b981' },
  { name: 'Travel', spent: 1800, budget: 2200, color: '#f97316' },
  { name: 'Shopping', spent: 1500, budget: 2000, color: '#ec4899' },
]

const monthlyTrend = [
  { month: 'Jan', value: 35 },
  { month: 'Feb', value: 48 },
  { month: 'Mar', value: 40 },
  { month: 'Apr', value: 62 },
  { month: 'May', value: 58 },
  { month: 'Jun', value: 75 },
  { month: 'Jul', value: 68 },
]

const timeBasedExpenses = {
  day: [
    { label: 'Mon', value: 1200, color: '#4f46e5' },
    { label: 'Tue', value: 900, color: '#6366f1' },
    { label: 'Wed', value: 1400, color: '#8b5cf6' },
    { label: 'Thu', value: 850, color: '#10b981' },
    { label: 'Fri', value: 1600, color: '#f59e0b' },
    { label: 'Sat', value: 2000, color: '#f97316' },
    { label: 'Sun', value: 1100, color: '#ec4899' },
  ],
  month: [
    { label: 'Jan', value: 2800, color: '#4f46e5' },
    { label: 'Feb', value: 2400, color: '#6366f1' },
    { label: 'Mar', value: 3100, color: '#8b5cf6' },
    { label: 'Apr', value: 2600, color: '#10b981' },
    { label: 'May', value: 3400, color: '#f59e0b' },
    { label: 'Jun', value: 3000, color: '#f97316' },
    { label: 'Jul', value: 2900, color: '#ec4899' },
  ],
  year: [
    { label: '2021', value: 22000, color: '#4f46e5' },
    { label: '2022', value: 26000, color: '#6366f1' },
    { label: '2023', value: 31000, color: '#10b981' },
    { label: '2024', value: 35000, color: '#f59e0b' },
    { label: '2025', value: 42000, color: '#f97316' },
  ],
}

function Insight() {
  const [selectedPeriod, setSelectedPeriod] = useState('month')

  const totalIncome = 24500
  const totalExpense = 16820
  const savings = totalIncome - totalExpense

  const selectedData = timeBasedExpenses[selectedPeriod]

  const pieChartStyle = useMemo(() => {
    let start = 0

    const gradientParts = selectedData.map((item) => {
      const end = start + (item.value / totalExpense) * 100
      const current = `${item.color} ${start}% ${end}%`
      start = end
      return current
    })

    return {
      background: `conic-gradient(${gradientParts.join(', ')})`,
    }
  }, [selectedData])

  const totalSelectedExpense = selectedData.reduce((sum, item) => sum + item.value, 0)

  return (
    <div className="app-container insight-app-container">
      <Sidebar activePage="insights" />

      <main className="main-content">
        <div className="dashboard-max-width">
          <section className="insight-section">
            <header className="insight-header">
              <div>
                <p className="section-kicker">Finance overview</p>
                <h1 className="section-title">Insights</h1>
              </div>

              <div className="filter-group" aria-label="Expense time filter">
                {['day', 'month', 'year'].map((period) => (
                  <button
                    key={period}
                    type="button"
                    className={`filter-button ${selectedPeriod === period ? 'active' : ''}`}
                    onClick={() => setSelectedPeriod(period)}
                  >
                    <TrendingUp size={16} />
                    {period.charAt(0).toUpperCase() + period.slice(1)}
                  </button>
                ))}
              </div>
            </header>

            <div className="insight-summary">
              {overviewStats.map(({ title, value, change, icon: Icon, accent, bg }) => (
                <div key={title} className="summary-card">
                  <div className="summary-icon" style={{ backgroundColor: bg, color: accent }}>
                    <Icon size={20} />
                  </div>

                  <div className="summary-text">
                    <span>{title}</span>
                    <strong>{value}</strong>
                    <small style={{ color: accent }}>{change}</small>
                  </div>
                </div>
              ))}
            </div>

            <div className="insight-grid">
              <div className="panel-card">
                <div className="panel-header">
                  <h2>Spending by category</h2>
                  <span>₹{totalExpense.toLocaleString('en-IN')}</span>
                </div>

                {categoryData.map((item) => {
                  const percentage = Math.round((item.spent / item.budget) * 100)

                  return (
                    <div key={item.name} className="category-row">
                      <div className="category-name-row">
                        <span>{item.name}</span>
                        <strong>₹{item.spent.toLocaleString('en-IN')}</strong>
                      </div>

                      <div className="progress-track">
                        <div
                          className="progress-fill"
                          style={{ width: `${percentage}%`, backgroundColor: item.color }}
                        />
                      </div>

                      <div className="category-meta">
                        <small>{percentage}% of budget</small>
                        <small>₹{(item.budget - item.spent).toLocaleString('en-IN')} left</small>
                      </div>
                    </div>
                  )
                })}
              </div>

              <div className="panel-card">
                <div className="panel-header">
                  <h2>Monthly trend</h2>
                  <span>7 months</span>
                </div>

                <div className="trend-chart">
                  {monthlyTrend.map((item) => (
                    <div key={item.month} className="trend-column">
                      <div className="trend-bar-wrap">
                        <div
                          className="trend-bar"
                          style={{ height: `${item.value}%` }}
                          title={`${item.month}: ${item.value}%`}
                        />
                      </div>
                      <span>{item.month}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="insight-bottom">
              <div className="panel-card">
                <div className="panel-header">
                  <h2>{selectedPeriod.charAt(0).toUpperCase() + selectedPeriod.slice(1)} expense split</h2>
                  <span>₹{totalSelectedExpense.toLocaleString('en-IN')}</span>
                </div>

                <div className="pie-chart-layout">
                  <div className="pie-chart" style={pieChartStyle} />

                  <div className="legend-list">
                    {selectedData.map((item) => (
                      <div key={item.label} className="legend-item">
                        <div className="legend-color" style={{ backgroundColor: item.color }} />
                        <span>{item.label}</span>
                        <strong>₹{item.value.toLocaleString('en-IN')}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="panel-card">
                <div className="panel-header">
                  <h2>Money summary</h2>
                </div>

                <div className="summary-box">
                  <div className="summary-row">
                    <span>Total income</span>
                    <strong>₹{totalIncome.toLocaleString('en-IN')}</strong>
                  </div>
                  <div className="summary-row">
                    <span>Total expenses</span>
                    <strong>₹{totalExpense.toLocaleString('en-IN')}</strong>
                  </div>
                  <div className="summary-row highlight">
                    <span>Net savings</span>
                    <strong>₹{savings.toLocaleString('en-IN')}</strong>
                  </div>
                </div>
              </div>
            </div>

            <div className="insight-tip-card panel-card">
              <div className="panel-header">
                <h2>Smart insight</h2>
              </div>

              <div className="tip-box">
                <Wallet size={22} />
                <p>
                  Your spending is under control this month. You are saving a healthy amount,
                  and food remains the biggest category to watch.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

export default Insight
