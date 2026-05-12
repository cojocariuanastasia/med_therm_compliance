import { useState, useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const parameterOptions = [
  { id: 'temperature', label: 'Temperature (C)', color: '#ef4444', unit: 'C', min: 0, max: 15 },
  { id: 'fan_speed', label: 'Fan Speed (RPM)', color: '#3b82f6', unit: 'RPM', min: 0, max: 4000 },
  { id: 'voltage', label: 'Voltage (V)', color: '#8b5cf6', unit: 'V', min: 10, max: 14 },
  { id: 'battery_level', label: 'Battery Level (%)', color: '#10b981', unit: '%', min: 0, max: 100 },
  { id: 'humidity', label: 'Humidity (%)', color: '#06b6d4', unit: '%', min: 0, max: 100 },
];

export default function TimelineChart({ data, violations }) {
  const [selectedParam, setSelectedParam] = useState('temperature');

  const paramConfig = parameterOptions.find(p => p.id === selectedParam);
  const paramData = data?.[selectedParam] || [];

  const chartData = useMemo(() => {
    if (!paramData || paramData.length === 0) {
      return {
        labels: [],
        datasets: [],
      };
    }

    const sortedData = [...paramData].sort((a, b) => 
      new Date(a.timestamp) - new Date(b.timestamp)
    );

    const labels = sortedData.map(d => {
      const ts = new Date(d.timestamp);
      return ts.toLocaleTimeString();
    });

    const values = sortedData.map(d => d.value);

    const violationTimestamps = violations
      .filter(v => v.timestamp)
      .map(v => new Date(v.timestamp).toLocaleTimeString());

    const backgroundColors = sortedData.map((d, i) => {
      const ts = new Date(d.timestamp).toLocaleTimeString();
      if (violationTimestamps.includes(ts)) {
        return 'rgba(239, 68, 68, 0.9)';
      }
      
      if (selectedParam === 'temperature') {
        if (d.value < 2 || d.value > 8) {
          return 'rgba(239, 68, 68, 0.8)';
        }
      }
      return paramConfig?.color || '#3b82f6';
    });

    const datasets = [{
      label: paramConfig?.label || selectedParam,
      data: values,
      borderColor: paramConfig?.color || '#3b82f6',
      backgroundColor: (context) => {
        const ctx = context.chart.ctx;
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, (paramConfig?.color || '#3b82f6') + '40');
        gradient.addColorStop(1, (paramConfig?.color || '#3b82f6') + '05');
        return gradient;
      },
      borderWidth: 2,
      fill: true,
      tension: 0.3,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: backgroundColors,
      pointBorderColor: '#fff',
      pointBorderWidth: 1,
    }];

    if (selectedParam === 'temperature') {
      datasets.push({
        label: 'Min Allowed (2C)',
        data: Array(labels.length).fill(2),
        borderColor: '#22c55e',
        borderWidth: 1,
        borderDash: [5, 5],
        pointRadius: 0,
        fill: false,
      });
      datasets.push({
        label: 'Max Allowed (8C)',
        data: Array(labels.length).fill(8),
        borderColor: '#ef4444',
        borderWidth: 1,
        borderDash: [5, 5],
        pointRadius: 0,
        fill: false,
      });
    }

    return { labels, datasets };
  }, [paramData, paramConfig, selectedParam, violations]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 20,
        }
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        padding: 12,
        titleFont: { size: 13, weight: 'bold' },
        bodyFont: { size: 12 },
        cornerRadius: 8,
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Time',
        },
        grid: {
          display: true,
          color: 'rgba(148, 163, 184, 0.1)',
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: paramConfig?.unit || '',
        },
        grid: {
          display: true,
          color: 'rgba(148, 163, 184, 0.1)',
        },
        ...(paramConfig?.min !== undefined && { min: paramConfig.min - 1 }),
        ...(paramConfig?.max !== undefined && { max: paramConfig.max + 1 }),
      }
    }
  };

  const eventSummary = useMemo(() => {
    return {
      doorEvents: data?.door_events?.length || 0,
      alarmEvents: data?.alarm_events?.length || 0,
      sensorTimeouts: data?.sensor_timeout?.length || 0,
      syncFailures: data?.sync_failed?.length || 0,
    };
  }, [data]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {parameterOptions.map(param => (
          <button
            key={param.id}
            onClick={() => setSelectedParam(param.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              selectedParam === param.id
                ? 'bg-slate-900 text-white shadow-lg'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <span className="inline-block w-3 h-3 rounded-full mr-2" style={{ backgroundColor: param.color }}></span>
            {param.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <p className="text-sm text-orange-600">Door Events</p>
          <p className="text-2xl font-bold text-orange-800">{eventSummary.doorEvents}</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-600">Alarms</p>
          <p className="text-2xl font-bold text-red-800">{eventSummary.alarmEvents}</p>
        </div>
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <p className="text-sm text-amber-600">Sensor Timeouts</p>
          <p className="text-2xl font-bold text-amber-800">{eventSummary.sensorTimeouts}</p>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
          <p className="text-sm text-slate-600">Sync Failures</p>
          <p className="text-2xl font-bold text-slate-800">{eventSummary.syncFailures}</p>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6" style={{ height: '500px' }}>
        {chartData.labels.length > 0 ? (
          <Line data={chartData} options={chartOptions} />
        ) : (
          <div className="flex items-center justify-center h-full text-slate-400">
            No data available for this parameter
          </div>
        )}
      </div>

      {selectedParam === 'temperature' && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-700">
            <strong>Legend:</strong> Red points indicate temperature readings outside the allowed range (2C-8C) or at timestamps where violations were detected. 
            Dashed green/red lines show minimum and maximum allowed temperature thresholds.
          </p>
        </div>
      )}
    </div>
  );
}
