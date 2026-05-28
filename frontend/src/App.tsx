import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Courts from './pages/Courts'
import Changes from './pages/Changes'
import Settings from './pages/Settings'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/courts" element={<Courts />} />
        <Route path="/changes" element={<Changes />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}
