export default function AlertsTable({ alerts }) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="card">
      <h3 className="card-title">Recent Alerts</h3>
      <div className="table-wrapper">
        <table className="alerts-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>City</th>
              <th>Zone</th>
              <th>Threat</th>
              <th>Countdown</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert, i) => (
              <tr key={alert.rid || i}>
                <td className="table-time">{alert.time}</td>
                <td>
                  <span className="table-city">{alert.name_en || alert.name}</span>
                </td>
                <td className="table-zone">{alert.zone_en || alert.zone}</td>
                <td>
                  <span className={`threat-badge threat-${alert.threat}`}>
                    {alert.threatName_en || alert.threatName || `Type ${alert.threat}`}
                  </span>
                </td>
                <td className="table-countdown">{alert.countdown}s</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
