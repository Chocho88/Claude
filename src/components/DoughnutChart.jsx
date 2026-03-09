import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6'];

export default function DoughnutChart({ data, title }) {
  const chartData = {
    labels: data.map(d => d.name || d.label),
    datasets: [
      {
        data: data.map(d => d.count),
        backgroundColor: COLORS.slice(0, data.length),
        borderColor: '#0f172a',
        borderWidth: 2,
        hoverOffset: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: { color: '#e2e8f0', padding: 12, usePointStyle: true, pointStyleWidth: 10, font: { size: 12 } },
      },
      title: { display: true, text: title, color: '#e2e8f0', font: { size: 14, weight: '600' } },
      tooltip: {
        backgroundColor: '#1e293b',
        titleColor: '#e2e8f0',
        bodyColor: '#94a3b8',
        borderColor: '#334155',
        borderWidth: 1,
      },
    },
  };

  return (
    <div className="chart-container">
      <Doughnut data={chartData} options={options} />
    </div>
  );
}
