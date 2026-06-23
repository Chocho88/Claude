import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function BarChart({ data, title, color = '#ef4444', horizontal = false, maxItems = 15 }) {
  const sliced = data.slice(0, maxItems);

  const chartData = {
    labels: sliced.map(d => d.name || d.label),
    datasets: [
      {
        label: 'Alerts',
        data: sliced.map(d => d.count),
        backgroundColor: typeof color === 'string'
          ? sliced.map((_, i) => {
              const opacity = 1 - (i / sliced.length) * 0.5;
              return color.startsWith('#')
                ? `${color}${Math.round(opacity * 255).toString(16).padStart(2, '0')}`
                : color;
            })
          : color,
        borderColor: 'transparent',
        borderRadius: 4,
      },
    ],
  };

  const options = {
    indexAxis: horizontal ? 'y' : 'x',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      title: { display: true, text: title, color: '#e2e8f0', font: { size: 14, weight: '600' } },
      tooltip: {
        backgroundColor: '#1e293b',
        titleColor: '#e2e8f0',
        bodyColor: '#94a3b8',
        borderColor: '#334155',
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        ticks: { color: '#94a3b8', maxRotation: horizontal ? 0 : 45 },
        grid: { color: 'rgba(148, 163, 184, 0.1)' },
        beginAtZero: true,
      },
      y: {
        ticks: { color: '#94a3b8' },
        grid: { color: 'rgba(148, 163, 184, 0.1)' },
        beginAtZero: true,
      },
    },
  };

  return (
    <div className="chart-container">
      <Bar data={chartData} options={options} />
    </div>
  );
}
