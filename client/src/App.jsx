import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Login from './Login'
import Signup from './Signup'
import Dashboard from './Dashboard'
import Onboarding from './Onboarding'
import Category from './Category'
import Transaction from './Transaction'
import Budget from './Budget'
import Insight from './Insight'
import UPIPay from './UPIPay'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/category" element={<Category />} />
        <Route path="/transactions" element={<Transaction />} />
        <Route path="/budget" element={<Budget />} />
        <Route path="/budgets" element={<Budget />} />
        <Route path="/insights" element={<Insight />} />
        <Route path="/upi-pay" element={<UPIPay />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
