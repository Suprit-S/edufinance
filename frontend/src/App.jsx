import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import NotFoundPage from './pages/NotFoundPage'
import PlaceholderPage from './pages/PlaceholderPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="plan" element={<PlaceholderPage page="plan" />} />
        <Route path="wallets" element={<PlaceholderPage page="wallets" />} />
        <Route path="remittances" element={<PlaceholderPage page="remittances" />} />
        <Route path="target" element={<PlaceholderPage page="target" />} />
        <Route path="loans" element={<PlaceholderPage page="loans" />} />
        <Route path="reports" element={<PlaceholderPage page="reports" />} />
        <Route path="profile" element={<PlaceholderPage page="profile" />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
