import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import MainLayout from "./layout/MainLayout";
import Dashboard from "./pages/Dashboard";
import GraphView from "./pages/GraphView";
import Cases from "./pages/Cases";
import Alerts from "./pages/Alerts";
import Reports from "./pages/Reports";
import Profile from "./pages/Profile";
import Documentation from "./pages/Documentation";
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="graph/:account_id" element={<GraphView />} />
          <Route path="cases" element={<Cases />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="reports" element={<Reports />} />
           <Route path="profile" element={<Profile />} />
              <Route path="docs" element={<Documentation/>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
