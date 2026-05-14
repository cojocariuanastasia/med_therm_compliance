import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle, XCircle, AlertTriangle, Download, FileText, BarChart3, Clock, AlertCircle, ChevronRight, Loader2 } from 'lucide-react';
import { api } from '../api';
import TimelineChart from './TimelineChart';

export default function AnalysisResults({ file, onBack }) {
  const [analysis, setAnalysis] = useState(null);
  const [violations, setViolations] = useState([]);
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');
  const [hasSimulatedLogs, setHasSimulatedLogs] = useState(false);
  const [generatingLogs, setGeneratingLogs] = useState(false);

  useEffect(() => {
    loadAnalysis();
  }, [file]);

  const loadAnalysis = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await api.analyzeFile(file.id);
      
      if (result.success) {
        setAnalysis(result.analysis);
        setViolations(result.violations || []);
        
        if (result.analysis) {
          const timelineResult = await api.getTimeline(result.analysis.id);
          if (timelineResult.success) {
            setTimeline(timelineResult.timeline);
          }

          if (result.analysis.analysis_type === 'image') {
            const logsResult = await api.checkHasLogs(result.analysis.id);
            if (logsResult.success) {
              setHasSimulatedLogs(logsResult.has_simulated_logs);
            }
          }
        }
      } else {
        setError(result.error || 'Analysis failed');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to analyze file');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateLogs = async () => {
    if (!analysis) return;
    
    setGeneratingLogs(true);
    try {
      const result = await api.generateLogs(analysis.id);
      if (result.success) {
        setAnalysis(result.analysis);
        setViolations(result.violations || []);
        setHasSimulatedLogs(true);
        
        const timelineResult = await api.getTimeline(result.analysis.id);
        if (timelineResult.success) {
          setTimeline(timelineResult.timeline);
        }
      } else {
        setError(result.error || 'Failed to generate logs');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate logs');
    } finally {
      setGeneratingLogs(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString();
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'major': return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'warning': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return <XCircle className="h-5 w-5 text-red-500" />;
      case 'major': return <AlertTriangle className="h-5 w-5 text-amber-500" />;
      case 'warning': return <AlertCircle className="h-5 w-5 text-blue-500" />;
      default: return null;
    }
  };

  const groupViolationsBySeverity = () => {
    const groups = { critical: [], major: [], warning: [] };
    violations.forEach(v => {
      if (groups[v.severity]) {
        groups[v.severity].push(v);
      }
    });
    return groups;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12">
        <div className="text-center">
          <Loader2 className="h-12 w-12 text-primary-600 animate-spin mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">Analyzing File...</h3>
          <p className="text-slate-500">Running compliance checks against all 22 MED-THERM-2026 rules</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">Analysis Failed</h3>
          <p className="text-slate-500 mb-4">{error}</p>
          <button
            onClick={onBack}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const violationGroups = groupViolationsBySeverity();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center space-x-2 text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ChevronRight className="h-4 w-4 rotate-180" />
          <span>Back to Upload</span>
        </button>
        
        {analysis && (
          <div className="flex items-center space-x-2">
            <a
              href={api.getCsvDownloadUrl(analysis.id)}
              className="flex items-center space-x-2 px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
            >
              <Download className="h-4 w-4" />
              <span>CSV</span>
            </a>
            {analysis.analysis_type === 'image' && (
              <>
                {hasSimulatedLogs ? (
                  <a
                    href={api.getLogsDownloadUrl(analysis.id)}
                    className="flex items-center space-x-2 px-4 py-2 border border-emerald-500 text-emerald-700 rounded-lg text-sm font-medium hover:bg-emerald-50 transition-colors"
                  >
                    <FileText className="h-4 w-4" />
                    <span>Simulated Logs</span>
                  </a>
                ) : (
                  <button
                    onClick={handleGenerateLogs}
                    disabled={generatingLogs}
                    className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {generatingLogs ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <FileText className="h-4 w-4" />
                    )}
                    <span>{generatingLogs ? 'Generating...' : 'Generate Logs'}</span>
                  </button>
                )}
              </>
            )}
            <a
              href={api.getPdfDownloadUrl(analysis.id)}
              className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
            >
              <FileText className="h-4 w-4" />
              <span>PDF Report</span>
            </a>
          </div>
        )}
      </div>

      <div className={`rounded-xl shadow-sm border-2 p-6 ${
        analysis?.compliant 
          ? 'bg-green-50 border-green-300' 
          : 'bg-red-50 border-red-300'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {analysis?.compliant ? (
              <CheckCircle className="h-12 w-12 text-green-500" />
            ) : (
              <XCircle className="h-12 w-12 text-red-500" />
            )}
            <div>
              <h2 className="text-2xl font-bold text-slate-900">
                {analysis?.compliant ? 'COMPLIANT' : 'NON-COMPLIANT'}
              </h2>
              <p className="text-slate-600 mt-1">{file.original_filename}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">{violationGroups.critical.length}</p>
              <p className="text-sm text-slate-500">Critical</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-amber-600">{violationGroups.major.length}</p>
              <p className="text-sm text-slate-500">Major</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{violationGroups.warning.length}</p>
              <p className="text-sm text-slate-500">Warnings</p>
            </div>
          </div>
        </div>
        
        {analysis?.summary && (
          <p className="mt-4 text-slate-700">{analysis.summary}</p>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        <div className="border-b border-slate-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {[
              { id: 'summary', label: 'Summary', icon: BarChart3 },
              { id: 'violations', label: 'Violations', icon: AlertTriangle },
              { id: 'timeline', label: 'Timeline', icon: Clock },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'summary' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center space-x-3">
                    <XCircle className="h-8 w-8 text-red-500" />
                    <div>
                      <p className="text-3xl font-bold text-red-700">{violationGroups.critical.length}</p>
                      <p className="text-sm text-red-600">Critical Violations</p>
                    </div>
                  </div>
                </div>
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <div className="flex items-center space-x-3">
                    <AlertTriangle className="h-8 w-8 text-amber-500" />
                    <div>
                      <p className="text-3xl font-bold text-amber-700">{violationGroups.major.length}</p>
                      <p className="text-sm text-amber-600">Major Violations</p>
                    </div>
                  </div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center space-x-3">
                    <AlertCircle className="h-8 w-8 text-blue-500" />
                    <div>
                      <p className="text-3xl font-bold text-blue-700">{violationGroups.warning.length}</p>
                      <p className="text-sm text-blue-600">Warnings</p>
                    </div>
                  </div>
                </div>
              </div>

              {violations.length > 0 ? (
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-4">Top Violations</h3>
                  <div className="space-y-3">
                    {violations.slice(0, 5).map((violation, idx) => (
                      <div key={idx} className={`p-4 rounded-lg border ${getSeverityColor(violation.severity)}`}>
                        <div className="flex items-start space-x-3">
                          {getSeverityIcon(violation.severity)}
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold">{violation.regulation_code}: {violation.regulation_title}</span>
                              <span className="text-xs uppercase font-medium px-2 py-1 rounded bg-white bg-opacity-50">
                                {violation.severity}
                              </span>
                            </div>
                            <p className="text-sm mt-1">{violation.description}</p>
                            {violation.line_number && (
                              <p className="text-xs mt-1 opacity-70">Line {violation.line_number}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900 mb-2">All Checks Passed</h3>
                  <p className="text-slate-500">No violations detected against MED-THERM-2026 regulations.</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'violations' && (
            <div className="space-y-6">
              {violations.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900 mb-2">No Violations</h3>
                  <p className="text-slate-500">All compliance checks passed successfully.</p>
                </div>
              ) : (
                ['critical', 'major', 'warning'].map((severity) => {
                  const sevViolations = violationGroups[severity];
                  if (sevViolations.length === 0) return null;
                  
                  return (
                    <div key={severity}>
                      <h3 className={`text-lg font-semibold mb-3 ${
                        severity === 'critical' ? 'text-red-700' :
                        severity === 'major' ? 'text-amber-700' : 'text-blue-700'
                      }`}>
                        {severity.charAt(0).toUpperCase() + severity.slice(1)} ({sevViolations.length})
                      </h3>
                      <div className="space-y-3">
                        {sevViolations.map((violation, idx) => (
                          <div key={idx} className={`p-4 rounded-lg border ${getSeverityColor(violation.severity)}`}>
                            <div className="flex items-start space-x-3">
                              {getSeverityIcon(violation.severity)}
                              <div className="flex-1">
                                <div className="flex items-center justify-between">
                                  <span className="font-semibold">{violation.regulation_code}: {violation.regulation_title}</span>
                                  {violation.line_number && (
                                    <span className="text-xs opacity-70">Line {violation.line_number}</span>
                                  )}
                                </div>
                                <p className="text-sm mt-2">{violation.description}</p>
                                
                                {violation.evidence && (
                                  <details className="mt-2">
                                    <summary className="text-xs font-medium cursor-pointer hover:underline">View Evidence</summary>
                                    <pre className="mt-2 p-2 bg-white bg-opacity-50 rounded text-xs overflow-x-auto">
                                      {violation.evidence}
                                    </pre>
                                  </details>
                                )}
                                
                                <details className="mt-2">
                                  <summary className="text-xs font-medium cursor-pointer hover:underline">Regulation Reference</summary>
                                  <p className="mt-2 text-xs italic bg-white bg-opacity-50 p-2 rounded">
                                    "{violation.regulation_text}"
                                  </p>
                                </details>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}

          {activeTab === 'timeline' && (
            <div>
              {timeline ? (
                <TimelineChart data={timeline} violations={violations} />
              ) : (
                <div className="text-center py-12">
                  <Loader2 className="h-8 w-8 text-slate-400 animate-spin mx-auto" />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
