import { useState, useCallback } from 'react';
import { Upload, FileText, Image, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { api } from '../api';
import { useNavigate } from 'react-router-dom';

export default function FileUpload({ onUploadComplete }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const navigate = useNavigate();

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const validateFile = (file) => {
    const allowedTypes = ['text/plain', 'image/png', 'image/jpeg'];
    const allowedExtensions = ['.txt', '.png', '.jpg', '.jpeg'];
    
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(ext)) {
      return { valid: false, message: 'Invalid file type. Please upload TXT, PNG, or JPG files.' };
    }
    
    if (file.size > 50 * 1024 * 1024) {
      return { valid: false, message: 'File too large. Maximum size is 50MB.' };
    }
    
    return { valid: true };
  };

  const handleFileSelect = useCallback((file) => {
    setError(null);
    const validation = validateFile(file);
    if (!validation.valid) {
      setError(validation.message);
      return;
    }
    setSelectedFile(file);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleInputChange = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    setUploading(true);
    setProgress(0);
    setError(null);
    
    try {
      const result = await api.uploadFile(selectedFile, setProgress);
      
      if (result.success) {
        if (onUploadComplete) {
          onUploadComplete(result.file);
        }
      } else {
        setError(result.error || 'Upload failed');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    if (ext === 'txt') {
      return <FileText className="h-8 w-8 text-blue-500" />;
    }
    return <Image className="h-8 w-8 text-green-500" />;
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
        <div className="text-center mb-6">
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Upload a File</h2>
          <p className="text-slate-500">
            Upload log files (TXT) or temperature profile graphs (PNG/JPG) for compliance analysis
          </p>
        </div>

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer ${
            isDragging
              ? 'border-primary-500 bg-primary-50'
              : 'border-slate-300 hover:border-primary-400 hover:bg-slate-50'
          }`}
        >
          <input
            type="file"
            accept=".txt,.png,.jpg,.jpeg"
            onChange={handleInputChange}
            className="hidden"
            id="file-input"
            disabled={uploading}
          />
          <label htmlFor="file-input" className="cursor-pointer">
            <Upload className={`h-12 w-12 mx-auto mb-4 ${isDragging ? 'text-primary-500' : 'text-slate-400'}`} />
            <p className="text-lg font-medium text-slate-700 mb-2">
              {isDragging ? 'Drop your file here' : 'Drag and drop your file here'}
            </p>
            <p className="text-sm text-slate-500">or click to browse</p>
            <p className="text-xs text-slate-400 mt-2">
              Supported formats: TXT, PNG, JPG (Max 50MB)
            </p>
          </label>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {selectedFile && (
          <div className="mt-6">
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getFileIcon(selectedFile.name)}
                  <div>
                    <p className="font-medium text-slate-900">{selectedFile.name}</p>
                    <p className="text-sm text-slate-500">{formatFileSize(selectedFile.size)}</p>
                  </div>
                </div>
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="px-6 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Uploading {progress}%</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      <span>Upload & Analyze</span>
                    </>
                  )}
                </button>
              </div>
              
              {uploading && (
                <div className="mt-4">
                  <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-600 transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
          <div className="flex items-start space-x-3">
            <FileText className="h-6 w-6 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900">Log Files (.txt)</h3>
              <p className="text-sm text-blue-700 mt-1">
                Parse system logs, detect temperature violations, sensor failures, alarm issues, data gaps, and door access frequency.
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-green-50 border border-green-200 rounded-xl p-5">
          <div className="flex items-start space-x-3">
            <Image className="h-6 w-6 text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-green-900">Graph Images (.png, .jpg)</h3>
              <p className="text-sm text-green-700 mt-1">
                Analyze temperature profile charts using OCR and chart extraction. Extract timelines and validate compliance.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
