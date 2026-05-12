import { useState } from 'react';
import FileUpload from '../components/FileUpload';
import AnalysisResults from '../components/AnalysisResults';
import { Activity, FileCheck, BarChart3, Shield } from 'lucide-react';

export default function HomePage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [showResults, setShowResults] = useState(false);

  const handleUploadComplete = (file) => {
    setSelectedFile(file);
    setShowResults(true);
  };

  const handleBack = () => {
    setShowResults(false);
    setSelectedFile(null);
  };

  return (
    <div className="space-y-8">
      {!showResults && (
        <>
          <div className="bg-gradient-to-r from-primary-600 to-primary-800 rounded-2xl p-8 text-white">
            <div className="max-w-3xl">
              <div className="flex items-center space-x-3 mb-4">
                <Activity className="h-8 w-8" />
                <h1 className="text-3xl font-bold">MED-THERM-2026 Compliance Analyzer</h1>
              </div>
              <p className="text-primary-100 text-lg mb-6">
                AI-driven compliance platform for medical device regulatory validation. 
                Upload log files or temperature profile graphs for automated compliance checking.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white bg-opacity-10 rounded-xl p-4 backdrop-blur">
                  <div className="flex items-center space-x-2 mb-2">
                    <FileCheck className="h-5 w-5" />
                    <span className="font-semibold">Log File Analysis</span>
                  </div>
                  <p className="text-sm text-primary-100">
                    Parse system logs and validate against all 22 regulatory rules
                  </p>
                </div>
                <div className="bg-white bg-opacity-10 rounded-xl p-4 backdrop-blur">
                  <div className="flex items-center space-x-2 mb-2">
                    <BarChart3 className="h-5 w-5" />
                    <span className="font-semibold">Graph Analysis</span>
                  </div>
                  <p className="text-sm text-primary-100">
                    OCR and chart extraction from temperature profile images
                  </p>
                </div>
                <div className="bg-white bg-opacity-10 rounded-xl p-4 backdrop-blur">
                  <div className="flex items-center space-x-2 mb-2">
                    <Shield className="h-5 w-5" />
                    <span className="font-semibold">Report Generation</span>
                  </div>
                  <p className="text-sm text-primary-100">
                    Export compliance reports in CSV and PDF formats
                  </p>
                </div>
              </div>
            </div>
          </div>

          <FileUpload onUploadComplete={handleUploadComplete} />
        </>
      )}

      {showResults && selectedFile && (
        <AnalysisResults file={selectedFile} onBack={handleBack} />
      )}
    </div>
  );
}
