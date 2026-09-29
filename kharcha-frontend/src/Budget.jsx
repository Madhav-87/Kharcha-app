import { useState } from 'react'
import {
  BanknoteArrowDown,
  BanknoteArrowUp,
  Bus,
  Gamepad2,
  Home,
  Plus,
  ShoppingBag,
  Sparkles,
  Utensils,
} from 'lucide-react'
import Sidebar from './Sidebar'
import './Budget.css'

const initialBudgets = [
  { id: 1, name: 'Food', spent: 2450, limit: 3000, color: '#4f46e5', icon: Utensils },
  { id: 2, name: 'Transport', spent: 980, limit: 1500, color: '#f97316', icon: Bus },
  { id: 3, name: 'Rent', spent: 2100, limit: 2600, color: '#10b981', icon: Home },
  { id: 4, name: 'Shopping', spent: 1200, limit: 2000, color: '#ec4899', icon: ShoppingBag },
  { id: 5, name: 'Fun', spent: 700, limit: 1200, color: '#f59e0b', icon: Gamepad2 },
]

function Budget() {
  const [budgets, setBudgets] = useState(initialBudgets)
  const [showForm, setShowForm] = useState(false)
  const [categoryName, setCategoryName] = useState('')
  const [limitAmount, setLimitAmount] = useState('')

  const totalBudget = budgets.reduce((sum, item) => sum + item.limit, 0)
  const totalSpent = budgets.reduce((sum, item) => sum + item.spent, 0)
  const remaining = totalBudget - totalSpent

  const handleAddBudget = (event) => {
    event.preventDefault()

    if (!categoryName.trim() || !limitAmount) {
      return
    }

    const newBudget = {
      id: Date.now(),
      name: categoryName.trim(),
      spent: 0,
      limit: Number(limitAmount),
      color: '#22c55e',
      icon: Sparkles,
    }

    setBudgets((currentBudgets) => [...currentBudgets, newBudget])
    setCategoryName('')
    setLimitAmount('')
    setShowForm(false)
  }

  return (
    <div className="app-container budget-app-container">
      <Sidebar activePage="budgets" />

      <main className="main-content">
        <div className="dashboard-max-width">
          <section className="budget-section">
            <header className="budget-header">
              <div>
                <p className="section-label">Monthly planning</p>
                <h1 className="section-title">Budget</h1>
              </div>

              <button
                type="button"
                className="add-budget-btn"
                onClick={() => setShowForm((currentValue) => !currentValue)}
              >
                <Plus size={18} />
                {showForm ? 'Close' : 'Add budget'}
              </button>
            </header>

            {showForm && (
              <form className="budget-form" onSubmit={handleAddBudget}>
                <div className="input-group">
                  <label htmlFor="categoryName">Category name</label>
                  <input
                    id="categoryName"
                    type="text"
                    value={categoryName}
                    onChange={(event) => setCategoryName(event.target.value)}
                    placeholder="Example: Study"
                  />
                </div>

                <div className="input-group">
                  <label htmlFor="limitAmount">Budget limit</label>
                  <input
                    id="limitAmount"
                    type="number"
                    value={limitAmount}
                    onChange={(event) => setLimitAmount(event.target.value)}
                    placeholder="5000"
                    min="0"
                  />
                </div>

                <button type="submit" className="save-budget-btn">
                  Save budget
                </button>
              </form>
            )}

            <div className="budget-summary">
              <div className="summary-card">
                <div className="summary-icon budget-income">
                  <BanknoteArrowUp size={22} />
                </div>
                <div>
                  <span>Total budget</span>
                  <strong>₹{totalBudget.toLocaleString('en-IN')}</strong>
                </div>
              </div>

              <div className="summary-card">
                <div className="summary-icon budget-spent">
                  <BanknoteArrowDown size={22} />
                </div>
                <div>
                  <span>Spent</span>
                  <strong>₹{totalSpent.toLocaleString('en-IN')}</strong>
                </div>
              </div>

              <div className="summary-card">
                <div className="summary-icon budget-left">
                  <Sparkles size={22} />
                </div>
                <div>
                  <span>Left</span>
                  <strong>₹{remaining.toLocaleString('en-IN')}</strong>
                </div>
              </div>
            </div>

            <div className="budget-grid">
              <div className="budget-list-card">
                <h2>Budget categories</h2>

                {budgets.map((budget) => {
                  const Icon = budget.icon
                  const progress = budget.limit === 0 ? 0 : Math.min((budget.spent / budget.limit) * 100, 100)
                  const leftAmount = budget.limit - budget.spent
                  const isNearLimit = progress >= 80

                  return (
                    <div key={budget.id} className="budget-item">
                      <div className="budget-item-header">
                        <div className="budget-name-wrap">
                          <div
                            className="budget-icon"
                            style={{ backgroundColor: `${budget.color}22`, color: budget.color }}
                          >
                            <Icon size={18} />
                          </div>

                          <div>
                            <h3>{budget.name}</h3>
                            <p>
                              ₹{budget.spent.toLocaleString('en-IN')} of ₹{budget.limit.toLocaleString('en-IN')}
                            </p>
                          </div>
                        </div>

                        <span className={`status-badge ${isNearLimit ? 'warning' : 'good'}`}>
                          {isNearLimit ? 'Near limit' : 'On track'}
                        </span>
                      </div>

                      <div className="progress-track">
                        <div
                          className="progress-fill"
                          style={{ width: `${progress}%`, backgroundColor: budget.color }}
                        />
                      </div>

                      <div className="budget-amounts">
                        <span>₹{leftAmount.toLocaleString('en-IN')} left</span>
                        <span>{Math.round(progress)}%</span>
                      </div>
                    </div>
                  )
                })}
              </div>

              <div className="budget-tips-card">
                <h2>Smart tips</h2>

                <ul className="tips-list">
                  <li>Keep your food budget below 35% of your monthly income.</li>
                  <li>Save at least 10% for emergencies and future goals.</li>
                  <li>Review your budget every week to stay in control.</li>
                </ul>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

export default Budget
