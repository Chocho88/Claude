import { useState } from 'react';
import { useAlerts } from '../hooks/useAlerts';
import StatCard from './StatCard';
import TimelineChart from './TimelineChart';
import BarChart from './BarChart';
import DoughnutChart from './DoughnutChart';
import AlertsTable from './AlertsTable';
import { format } from 'date-fns';

export default function Dashboard() {
  const { stats, loading, error, isLiveData } = useAlerts();
  const [timeView, setTimeView] = useState('monthly');

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>Loading siren data...</p>
      </div>
    );
  }

  if (!stats) {
    return <div className="loading"><p>No data available.</p></div>;
  }

  const timeData = timeView === 'monthly' ? stats.byMonth : stats.byDay;
  const topCity = stats.byCity[0];
  const topZone = stats.byZone[0];

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1 className="dashboard-title">Israel Siren Statistics</h1>
          <p className="dashboard-subtitle">
            Powered by Tzofar (Tzeva Adom) alert data
          </p>
        </div>
        {error && (
          <div className="data-banner sample-banner">{error}</div>
        )}
        {isLiveData && (
          <div className="data-banner live-banner">Connected to live Tzofar data</div>
        )}
      </header>

      {/* Summary Cards */}
      <section className="stat-cards">
        <StatCard
          title="Total Alerts"
          value={stats.totalAlerts}
          subtitle={stats.dateRange.start ? `Since ${format(stats.dateRange.start, 'MMM yyyy')}` : ''}
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22c1.1 0 2-.9 2-2h-4a2 2 0 0 0 2 2z"/><path d="M18 16v-5c0-3.07-1.63-5.64-4.5-6.32V4a1.5 1.5 0 0 0-3 0v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>}
        />
        <StatCard
          title="Most Targeted City"
          value={topCity ? topCity.name : 'N/A'}
          subtitle={topCity ? `${topCity.count.toLocaleString()} alerts` : ''}
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>}
        />
        <StatCard
          title="Most Targeted Zone"
          value={topZone ? topZone.name : 'N/A'}
          subtitle={topZone ? `${topZone.count.toLocaleString()} alerts` : ''}
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 3v18"/></svg>}
        />
        <StatCard
          title="Drills"
          value={stats.totalDrills}
          subtitle={stats.totalAlerts ? `${((stats.totalDrills / stats.totalAlerts) * 100).toFixed(1)}% of total` : ''}
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>}
        />
      </section>

      {/* Timeline Section */}
      <section className="card">
        <div className="card-header">
          <h3 className="card-title">Alerts Over Time</h3>
          <div className="toggle-group">
            <button
              className={`toggle-btn ${timeView === 'monthly' ? 'active' : ''}`}
              onClick={() => setTimeView('monthly')}
            >
              Monthly
            </button>
            <button
              className={`toggle-btn ${timeView === 'daily' ? 'active' : ''}`}
              onClick={() => setTimeView('daily')}
            >
              Last 30 Days
            </button>
          </div>
        </div>
        <TimelineChart
          data={timeData}
          title=""
        />
      </section>

      {/* Charts Grid */}
      <section className="charts-grid">
        <div className="card">
          <BarChart
            data={stats.byCity}
            title="Top 15 Most Targeted Cities"
            horizontal={true}
            maxItems={15}
            color="#ef4444"
          />
        </div>
        <div className="card">
          <DoughnutChart
            data={stats.byThreat}
            title="Alert Types Breakdown"
          />
        </div>
      </section>

      <section className="charts-grid">
        <div className="card">
          <BarChart
            data={stats.byZone}
            title="Alerts by Region"
            horizontal={true}
            maxItems={13}
            color="#f97316"
          />
        </div>
        <div className="card">
          <BarChart
            data={stats.byHour}
            title="Alerts by Hour of Day"
            color="#3b82f6"
          />
        </div>
      </section>

      <section className="card">
        <BarChart
          data={stats.byDayOfWeek}
          title="Alerts by Day of Week"
          color="#8b5cf6"
        />
      </section>

      {/* Recent Alerts Table */}
      <AlertsTable alerts={stats.recentAlerts} />

      <footer className="dashboard-footer">
        <p>
          Data source: <a href="https://www.tzevaadom.co.il/en/" target="_blank" rel="noopener noreferrer">Tzofar (Tzeva Adom)</a>
          {' '}/ <a href="https://www.oref.org.il/" target="_blank" rel="noopener noreferrer">Pikud Haoref</a>
        </p>
        <p className="disclaimer">
          This is an unofficial tool for informational purposes only. Do not rely on this for life-safety decisions.
        </p>
      </footer>
    </div>
  );
}
