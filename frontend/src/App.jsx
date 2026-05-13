import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import FileHistory from './components/FileHistory';
import RulesPage from './components/RulesPage';
import AnalysisPage from './pages/AnalysisPage';

function App() {
  useEffect(() => {
    const handlePointerDown = (event) => {
      const activeElement = document.activeElement;

      if (!activeElement || activeElement === document.body) {
        return;
      }

      const clickedElement = event.target;
      const clickedInEditableControl = clickedElement.closest(
        'input, textarea, select, [contenteditable="true"]'
      );

      const activeIsEditableControl =
        activeElement.matches('input, textarea, select') ||
        activeElement.getAttribute('contenteditable') === 'true';

      if (!clickedInEditableControl && activeIsEditableControl) {
        activeElement.blur();
      }
    };

    document.addEventListener('pointerdown', handlePointerDown);

    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
    };
  }, []);

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
