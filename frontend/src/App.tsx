import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import MainLayout from './components/layout/MainLayout'
import Dashboard from './pages/Dashboard'
import Resources from './pages/ResourcesK8sGPT'
import Deployments from './pages/Deployments'
import Alerts from './pages/Alerts'
import Tickets from './pages/Tickets'
import Projects from './pages/Projects'
import AIAssistant from './pages/AIAssistant'
import Login from './pages/Login'
import Settings from './pages/Settings'

function App() {
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    )
  }

  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/resources" element={<Resources />} />
          <Route path="/resources/:regionId" element={<Resources />} />
          <Route path="/resources/:regionId/:clusterId" element={<Resources />} />
          <Route path="/deployments" element={<Deployments />} />
          <Route path="/deployments/:serviceId" element={<Deployments />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/tickets" element={<Tickets />} />
          <Route path="/tickets/:ticketId" element={<Tickets />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/ai-assistant" element={<AIAssistant />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  )
}

export default App
