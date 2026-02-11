import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Overview from './pages/Overview';
import Posts from './pages/Posts';
import RagActivity from './pages/RagActivity';
import Routing from './pages/Routing';
import Errors from './pages/Errors';
import KnowledgeBase from './pages/KnowledgeBase';
import BotLogic from './pages/BotLogic';
import Validation from './pages/Validation';
import './index.css';

// Protected route wrapper
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Overview />} />
          <Route path="posts" element={<Posts />} />
          <Route path="rag" element={<RagActivity />} />
          <Route path="knowledge" element={<KnowledgeBase />} />
          <Route path="routing" element={<Routing />} />
          <Route path="logic" element={<BotLogic />} />
          <Route path="validation" element={<Validation />} />
          <Route path="errors" element={<Errors />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
