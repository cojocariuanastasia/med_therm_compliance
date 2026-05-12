import { useState, useEffect } from 'react';
import { FileText, AlertTriangle, XCircle, AlertCircle, Search, Thermometer, Radio, Bell, Database, Battery, Wind, Shield, Activity, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '../api';

const categories = [
  { id: 'thermal', label: 'Thermal Safety', icon: Thermometer, color: 'text-red-600 bg-red-50' },
  { id: 'sensor', label: 'Sensor Redundancy', icon: Radio, color: 'text-amber-600 bg-amber-50' },
  { id: 'alarm', label: 'Alarm System', icon: Bell, color: 'text-orange-600 bg-orange-50' },
  { id: 'data', label: 'Data Integrity', icon: Database, color: 'text-blue-600 bg-blue-50' },
  { id: 'power', label: 'Power System', icon: Battery, color: 'text-green-600 bg-green-50' },
  { id: 'cooling', label: 'Cooling System', icon: Wind, color: 'text-cyan-600 bg-cyan-50' },
  { id: 'insulation', label: 'Insulation', icon: Shield, color: 'text-purple-600 bg-purple-50' },
  { id: 'operational', label: 'Operational', icon: Activity, color: 'text-slate-600 bg-slate-50' },
];

const severityInfo = {
  critical: { 
    icon: XCircle, 
    label: 'Critical',
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200'
  },
  major: { 
    icon: AlertTriangle, 
    label: 'Major',
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200'
  },
  warning: { 
    icon: AlertCircle, 
    label: 'Warning',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200'
  }
};

export default function RulesPage() {
  const [rules, setRules] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [expandedRule, setExpandedRule] = useState(null);

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      const result = await api.getRules();
      if (result.success) {
        setRules(result.rules);
      }
    } catch (err) {
      console.error('Failed to load rules');
    } finally {
      setLoading(false);
    }
  };

  const rulesArray = Object.values(rules);
  
  const filteredRules = rulesArray.filter(rule => {
    const matchesSearch = !searchTerm || 
      rule.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rule.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rule.text.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = !selectedCategory || rule.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  const groupedByCategory = categories.reduce((acc, cat) => {
    acc[cat.id] = filteredRules.filter(r => r.category === cat.id);
    return acc;
  }, {});

  const stats = {
    total: rulesArray.length,
    critical: rulesArray.filter(r => r.severity === 'critical').length,
    major: rulesArray.filter(r => r.severity === 'major').length,
    warning: rulesArray.filter(r => r.severity === 'warning').length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Regulatory Rules</h1>
          <p className="text-slate-500 mt-1">MED-THERM-2026 Compliance Standard for CryoSafe Plasma Transport Unit</p>
        </div>
        <div className="flex items-center space-x-2 bg-white border border-slate-200 rounded-lg px-4 py-2">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search rules..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="border-none outline-none text-sm w-48"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-primary-50 border border-primary-200 rounded-xl p-5">
          <div className="flex items-center space-x-3">
            <div className="bg-primary-100 p-2 rounded-lg">
              <FileText className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-primary-900">{stats.total}</p>
              <p className="text-sm text-primary-600">Total Rules</p>
            </div>
          </div>
        </div>
        {['critical', 'major', 'warning'].map(severity => {
          const info = severityInfo[severity];
          const Icon = info.icon;
          return (
            <div key={severity} className={`${info.bgColor} border ${info.borderColor} rounded-xl p-5`}>
              <div className="flex items-center space-x-3">
                <div className={`${info.bgColor} p-2 rounded-lg border ${info.borderColor}`}>
                  <Icon className={`h-5 w-5 ${info.color}`} />
                </div>
                <div>
                  <p className={`text-2xl font-bold ${info.color}`}>{stats[severity]}</p>
                  <p className={`text-sm ${info.color}`}>{info.label}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedCategory(null)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            selectedCategory === null
              ? 'bg-slate-900 text-white'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
          }`}
        >
          All Categories
        </button>
        {categories.map(cat => {
          const Icon = cat.icon;
          const count = groupedByCategory[cat.id]?.length || 0;
          return (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(selectedCategory === cat.id ? null : cat.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === cat.id
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span>{cat.label}</span>
              <span className={`px-1.5 py-0.5 rounded text-xs ${
                selectedCategory === cat.id ? 'bg-slate-700' : 'bg-slate-200'
              }`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      <div className="space-y-4">
        {filteredRules.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
            <Search className="h-12 w-12 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No Rules Found</h3>
            <p className="text-slate-500">Try adjusting your search or filter criteria.</p>
          </div>
        ) : (
          categories.map(cat => {
            const catRules = groupedByCategory[cat.id];
            if (!catRules || catRules.length === 0) return null;

            const Icon = cat.icon;
            return (
              <div key={cat.id} className="space-y-3">
                <div className="flex items-center space-x-2">
                  <div className={`p-1.5 rounded-lg ${cat.color.split(' ')[1]}`}>
                    <Icon className={`h-4 w-4 ${cat.color.split(' ')[0]}`} />
                  </div>
                  <h2 className="text-lg font-semibold text-slate-900">{cat.label}</h2>
                  <span className="text-sm text-slate-500">({catRules.length} rules)</span>
                </div>
                
                <div className="space-y-2">
                  {catRules.map(rule => {
                    const sevInfo = severityInfo[rule.severity];
                    const SevIcon = sevInfo.icon;
                    const isExpanded = expandedRule === rule.code;
                    
                    return (
                      <div
                        key={rule.code}
                        className={`bg-white rounded-lg border ${sevInfo.borderColor} overflow-hidden`}
                      >
                        <button
                          onClick={() => setExpandedRule(isExpanded ? null : rule.code)}
                          className="w-full p-4 flex items-center justify-between hover:bg-slate-50 transition-colors text-left"
                        >
                          <div className="flex items-center space-x-4">
                            <div className={`p-2 rounded-lg ${sevInfo.bgColor}`}>
                              <SevIcon className={`h-5 w-5 ${sevInfo.color}`} />
                            </div>
                            <div>
                              <div className="flex items-center space-x-2">
                                <span className="font-mono font-semibold text-slate-900">{rule.code}</span>
                                <span className={`text-xs font-medium px-2 py-0.5 rounded ${sevInfo.bgColor} ${sevInfo.color}`}>
                                  {rule.severity}
                                </span>
                              </div>
                              <p className="text-sm text-slate-600 mt-0.5">{rule.title}</p>
                            </div>
                          </div>
                          {isExpanded ? (
                            <ChevronUp className="h-5 w-5 text-slate-400" />
                          ) : (
                            <ChevronDown className="h-5 w-5 text-slate-400" />
                          )}
                        </button>
                        
                        {isExpanded && (
                          <div className="px-4 pb-4 pt-2 border-t border-slate-100">
                            <div className="bg-slate-50 rounded-lg p-4">
                              <p className="text-sm text-slate-700 leading-relaxed">
                                <strong className="text-slate-900">Regulation Text:</strong><br />
                                {rule.text}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
