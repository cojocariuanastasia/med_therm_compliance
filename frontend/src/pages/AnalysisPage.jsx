import { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import AnalysisResults from '../components/AnalysisResults';
import { api } from '../api';
import { Loader2, AlertCircle } from 'lucide-react';

export default function AnalysisPage() {
  const { fileId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  
  const [file, setFile] = useState(location.state?.file);
  const [loading, setLoading] = useState(!location.state?.file);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!file && fileId) {
      loadFile(fileId);
    }
  }, [fileId, file]);

  const loadFile = async (id) => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getFile(id);
      if (result.success) {
        setFile(result.file);
      } else {
        setError(result.error || 'File not found');
      }
    } catch (err) {
      setError('Failed to load file');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/history');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <Loader2 className="h-12 w-12 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Loading file...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-slate-900 mb-2">Error Loading File</h3>
        <p className="text-slate-500 mb-4">{error}</p>
        <button
          onClick={handleBack}
          className="px-6 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
        >
          Go to File History
        </button>
      </div>
    );
  }

  if (!file) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
        <AlertCircle className="h-12 w-12 text-slate-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-slate-900 mb-2">No File Selected</h3>
        <p className="text-slate-500 mb-4">Please select a file from the history or upload a new one.</p>
        <button
          onClick={handleBack}
          className="px-6 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
        >
          Go to File History
        </button>
      </div>
    );
  }

  return <AnalysisResults file={file} onBack={handleBack} />;
}
