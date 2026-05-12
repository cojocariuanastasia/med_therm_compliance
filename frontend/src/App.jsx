import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import FileHistory from './components/FileHistory';
import RulesPage from './components/RulesPage';
import AnalysisPage from './pages/AnalysisPage';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/history" element={<FileHistory />} />
          <Route path="/rules" element={<RulesPage />} />
          <Route path="/analysis/:fileId" element={<AnalysisPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
