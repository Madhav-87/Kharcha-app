import "./Dashboard.css"
import {
    LayoutDashboard,
    ReceiptText,
    PieChart,
    ArrowUpRight,
    BarChart2,
    Utensils,
    Bus,
    Tv,
    Home,
    ShoppingBag,
    Smartphone,
    Train,
    Bell,
    Plus,
    ArrowDownLeft,
    Sparkles,
    HelpCircle,
    Shapes
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

// ==========================================
// 1. DATA (Keep this outside to keep logic clean)
// ==========================================

const categoryData = [
    { id: 1, name: 'Food & cafés', amount: '2,410', icon: Utensils, progress: 80, color: '#4338ca' },
    { id: 2, name: 'Transport', amount: '1,180', icon: Bus, progress: 40, color: '#818cf8' },
    { id: 3, name: 'Subscriptions', amount: '640', icon: Tv, progress: 20, color: '#cbd5e1' },
    { id: 4, name: 'Rent share', amount: '2,610', icon: Home, progress: 85, color: '#f97316' },
];

const budgetData = [
    { id: 1, name: 'Food', spent: '2,410', total: '3,000', progress: 80, color: '#4338ca' },
    { id: 2, name: 'Fun & out', spent: '900', total: '1,000', progress: 90, color: '#f97316' },
    { id: 3, name: 'Savings', spent: '2,000', total: '3,000', progress: 66, color: '#10b981' },
];

const transactionData = [
    { id: 1, title: 'Swiggy · lunch', time: 'Today, 1:12 PM · Paid', amount: '-₹240', isPositive: false, icon: ShoppingBag, iconColor: '#4f46e5', iconBg: '#e0e7ff' },
    { id: 2, title: 'UPI · Utkarsh', time: 'Today, 9:40 AM · Received', amount: '+₹1,500', isPositive: true, icon: ArrowDownLeft, iconColor: '#059669', iconBg: '#d1fae5' },
    { id: 3, title: 'Airtel · recharge', time: 'Yesterday · Paid', amount: '-₹299', isPositive: false, icon: Smartphone, iconColor: '#ea580c', iconBg: '#ffedd5' },
    { id: 4, title: 'Metro · card top-up', time: '12 May · Paid', amount: '-₹150', isPositive: false, icon: Train, iconColor: '#475569', iconBg: '#f1f5f9' },
];

const chartData = [
    { day: 'M', height: '40%', active: false },
    { day: 'T', height: '55%', active: false },
    { day: 'W', height: '30%', active: false },
    { day: 'T', height: '65%', active: false },
    { day: 'F', height: '50%', active: false },
    { day: 'S', height: '90%', active: true },
    { day: 'S', height: '35%', active: false },
];

// ==========================================
// 2. CSS STYLES (Move this to dashboard.css in your real app)
// ==========================================


// ==========================================
// 3. REUSABLE MICRO-COMPONENTS
// ==========================================
const SidebarItem = ({ icon: Icon, label, isActive, path }) => {
    const navigate =useNavigate()
    return (
        <button className={`nav-item ${isActive ? 'active' : ''}`} onClick={() => navigate(path)}>
            <Icon size={20} />
            <span>{label}</span>
        </button>
    );

}

const ProgressBar = ({ progress, color }) => (
    <div className="progress-track" >
        <div className="progress-fill" style={{ width: `${progress}%`, backgroundColor: color }} />
    </div>
);


// ==========================================
// 4. MAIN DASHBOARD COMPONENT
// ==========================================
export default function Dashboard() {

    return (
        <>

            <div className="app-container">

                {/* === SIDEBAR === */}
                <aside className="sidebar">
                    <div>
                        <div className="sidebar-logo">
                            <div className="logo-circle">P</div>
                            <div>
                                <h1 style={{ fontSize: '18px', fontWeight: 'bold' }}>Paisa</h1>
                                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Student finance</p>
                            </div>
                        </div>

                        <nav className="sidebar-nav">
                            <SidebarItem icon={LayoutDashboard} label="Dashboard" isActive={true} path="#" />
                            <SidebarItem icon={ReceiptText} label="Transactions" isActive={false} path="/transactions" />
                            <SidebarItem icon={PieChart} label="Budgets" isActive={false} path="#" />
                            <SidebarItem icon={ArrowUpRight} label="UPI Pay" isActive={false} path="#" />
                            <SidebarItem icon={BarChart2} label="Insights" isActive={false} path="#" />
                            <SidebarItem icon={Shapes} label="Categories" isActive={false} path='/category' />
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

                {/* === MAIN CONTENT === */}
                <main className="main-content">
                    <div className="dashboard-max-width">

                        {/* Header */}
                        <header className="header">
                            <div>
                                <p className="header-date">Tuesday, 29 September</p>
                                <h2 className="header-greeting">Hi, Rahul</h2>
                            </div>

                            <div className="header-actions">
                                <div className="badge-upi">
                                    <div className="dot-green" />
                                    UPI linked
                                </div>
                                <button className="btn-icon">
                                    <Bell size={18} />
                                </button>
                                <div className="profile-circle">RS</div>
                            </div>
                        </header>

                        {/* Top Row: Balance & Actions */}
                        <div className="grid-top">
                            <div className="balance-card">
                                <div className="balance-circle-1" />
                                <div className="balance-circle-2" />

                                <p className="balance-label">Total balance</p>
                                <h1 className="balance-amount">₹18,420</h1>

                                <div className="balance-pills">
                                    <div className="pill">Savings ₹9,200</div>
                                    <div className="pill">Spendable ₹9,220</div>
                                </div>
                            </div>

                            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                                <p className="quick-action-label">Quick action</p>
                                <div>
                                    <button className="btn-primary">
                                        <ArrowUpRight size={18} /> Pay with UPI
                                    </button>
                                    <button className="btn-secondary">
                                        <Plus size={18} /> Add expense
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Middle Row: Charts & Categories */}
                        <div className="grid-middle">

                            {/* Spending Chart */}
                            <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
                                <div className="chart-header">
                                    <div>
                                        <h3 className="card-title" style={{ marginBottom: 0 }}>Spending this month</h3>
                                        <p className="chart-subtitle">₹6,840 spent · September</p>
                                    </div>
                                    <div className="badge-green">-12% vs Aug</div>
                                </div>

                                <div className="chart-area">
                                    {chartData.map((bar, index) => (
                                        <div key={index} className="bar-group">
                                            <div className="bar-track">
                                                <div
                                                    className={`bar-fill ${bar.active ? 'active' : ''}`}
                                                    style={{ height: bar.height }}
                                                />
                                            </div>
                                            <span className={`bar-label ${bar.active ? 'active' : ''}`}>
                                                {bar.day}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* By Category */}
                            <div className="card">
                                <h3 className="card-title">By category</h3>
                                <div>
                                    {categoryData.map((item) => (
                                        <div key={item.id} className="list-item">
                                            <div className="list-header">
                                                <div className="list-name">
                                                    <item.icon size={16} className="list-icon" />
                                                    {item.name}
                                                </div>
                                                <span className="list-amount">₹{item.amount}</span>
                                            </div>
                                            <ProgressBar progress={item.progress} color={item.color} />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Bottom Row: Budgets & Transactions */}
                        <div className="grid-bottom">

                            {/* Budget Progress */}
                            <div className="card">
                                <div className="tx-header">
                                    <h3 className="card-title" style={{ marginBottom: 0 }}>Budget progress</h3>
                                    <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 500 }}>September</span>
                                </div>
                                <div>
                                    {budgetData.map((budget) => (
                                        <div key={budget.id} className="list-item">
                                            <div className="list-header">
                                                <span className="list-name">{budget.name}</span>
                                                <span className="list-amount">
                                                    ₹{budget.spent} <span className="list-amount-muted">/ ₹{budget.total}</span>
                                                </span>
                                            </div>
                                            <ProgressBar progress={budget.progress} color={budget.color} />
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Recent Transactions */}
                            <div className="card">
                                <div className="tx-header">
                                    <h3 className="card-title" style={{ marginBottom: 0 }}>Recent transactions</h3>
                                    <button className="btn-text">
                                        View all <ArrowUpRight size={16} />
                                    </button>
                                </div>

                                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                    {transactionData.map((tx) => (
                                        <div key={tx.id} className="tx-item">
                                            <div className="tx-left">
                                                <div className="tx-icon-box" style={{ backgroundColor: tx.iconBg, color: tx.iconColor }}>
                                                    <tx.icon size={18} />
                                                </div>
                                                <div>
                                                    <p className="tx-title">{tx.title}</p>
                                                    <p className="tx-time">{tx.time}</p>
                                                </div>
                                            </div>
                                            <span className={`tx-amount ${tx.isPositive ? 'positive' : ''}`}>
                                                {tx.amount}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Bottom Alerts */}
                        <div className="grid-alerts">
                            <div className="alert-box alert-blue">
                                <div className="alert-icon-box"><Sparkles size={16} /></div>
                                <div>
                                    <h4 className="alert-title">Your money, at a glance</h4>
                                    <p className="alert-text">You're on track to keep ₹3,550 for the month. Transport is trending up slightly.</p>
                                </div>
                            </div>

                            <div className="alert-box alert-orange">
                                <div className="alert-icon-box"><HelpCircle size={16} /></div>
                                <div>
                                    <h4 className="alert-title">Food budget is 80% used</h4>
                                    <p className="alert-text">You have ₹590 left in this category for September.</p>
                                </div>
                            </div>
                        </div>

                    </div>
                </main>
            </div>
        </>
    );
}