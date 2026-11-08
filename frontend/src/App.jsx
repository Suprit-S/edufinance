import { Route, Routes } from 'react-router-dom'
import RequireAuth from './auth/RequireAuth'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import PlaceholderPage from './pages/PlaceholderPage'
import ProfilePage from './pages/ProfilePage'
import RegisterPage from './pages/RegisterPage'
import TransactionsPage from './pages/TransactionsPage'
import WalletDetailPage from './pages/WalletDetailPage'
import WalletsPage from './pages/WalletsPage'

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
          <Route path="plan" element={<PlaceholderPage page="plan" />} />
          <Route path="target" element={<PlaceholderPage page="target" />} />
          <Route path="remittances" element={<PlaceholderPage page="remittances" />} />
          <Route path="loans" element={<PlaceholderPage page="loans" />} />
          <Route path="reports" element={<PlaceholderPage page="reports" />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  )
}
