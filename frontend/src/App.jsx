import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import RequireAuth from './auth/RequireAuth'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import LoansPage from './pages/LoansPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import PlanPage from './pages/PlanPage'
import ProfilePage from './pages/ProfilePage'
import RegisterPage from './pages/RegisterPage'
import RemittancesPage from './pages/RemittancesPage'
import TransactionsPage from './pages/TransactionsPage'
import WalletDetailPage from './pages/WalletDetailPage'
import WalletsPage from './pages/WalletsPage'

// Pages with charts load the chart library only when opened (smaller first load).
const LoanDetailPage = lazy(() => import('./pages/LoanDetailPage'))
const TargetPage = lazy(() => import('./pages/TargetPage'))
const ReportsPage = lazy(() => import('./pages/ReportsPage'))

const loading = <p className="status-line">Loading…</p>

export default function App() {
  return (
    <Routes>
      <Route path="login" element={<LoginPage />} />
      <Route path="register" element={<RegisterPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="wallets" element={<WalletsPage />} />
          <Route path="wallets/:walletId" element={<WalletDetailPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="plan" element={<PlanPage />} />
          <Route path="target" element={<Suspense fallback={loading}><TargetPage /></Suspense>} />
          <Route path="remittances" element={<RemittancesPage />} />
          <Route path="loans" element={<LoansPage />} />
          <Route path="loans/:loanId" element={<Suspense fallback={loading}><LoanDetailPage /></Suspense>} />
          <Route path="reports" element={<Suspense fallback={loading}><ReportsPage /></Suspense>} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  )
}
