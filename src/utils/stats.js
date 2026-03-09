import { format, parseISO, startOfMonth, startOfWeek, startOfDay } from 'date-fns';

export function parseAlertDate(alert) {
  if (alert.datetime) return new Date(alert.datetime);
  // Parse "DD.MM.YYYY HH:MM:SS" format
  const [datePart, timePart] = alert.time.split(' ');
  const [d, m, y] = datePart.split('.');
  return new Date(`${y}-${m}-${d}T${timePart}`);
}

export function computeStats(alerts) {
  if (!alerts || alerts.length === 0) {
    return {
      totalAlerts: 0,
      totalDrills: 0,
      byCity: [],
      byZone: [],
      byThreat: [],
      byMonth: [],
      byDay: [],
      byHour: [],
      byDayOfWeek: [],
      recentAlerts: [],
      dateRange: { start: null, end: null },
    };
  }

  const totalAlerts = alerts.length;
  const totalDrills = alerts.filter(a => a.isDrill).length;

  // Date range
  const dates = alerts.map(a => parseAlertDate(a));
  const start = new Date(Math.min(...dates));
  const end = new Date(Math.max(...dates));

  // By city
  const cityMap = {};
  alerts.forEach(a => {
    const key = a.name_en || a.name;
    cityMap[key] = (cityMap[key] || 0) + 1;
  });
  const byCity = Object.entries(cityMap)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);

  // By zone
  const zoneMap = {};
  alerts.forEach(a => {
    const key = a.zone_en || a.zone;
    zoneMap[key] = (zoneMap[key] || 0) + 1;
  });
  const byZone = Object.entries(zoneMap)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);

  // By threat type
  const threatMap = {};
  alerts.forEach(a => {
    const key = a.threatName_en || a.threatName || `Type ${a.threat}`;
    threatMap[key] = (threatMap[key] || 0) + 1;
  });
  const byThreat = Object.entries(threatMap)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);

  // By month
  const monthMap = {};
  alerts.forEach(a => {
    const d = parseAlertDate(a);
    const key = format(startOfMonth(d), 'yyyy-MM');
    monthMap[key] = (monthMap[key] || 0) + 1;
  });
  const byMonth = Object.entries(monthMap)
    .map(([month, count]) => ({ month, label: format(new Date(month + '-01'), 'MMM yyyy'), count }))
    .sort((a, b) => a.month.localeCompare(b.month));

  // By day (last 30 days)
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
  const dayMap = {};
  alerts.forEach(a => {
    const d = parseAlertDate(a);
    if (d >= thirtyDaysAgo) {
      const key = format(startOfDay(d), 'yyyy-MM-dd');
      dayMap[key] = (dayMap[key] || 0) + 1;
    }
  });
  const byDay = Object.entries(dayMap)
    .map(([day, count]) => ({ day, label: format(new Date(day), 'MMM dd'), count }))
    .sort((a, b) => a.day.localeCompare(b.day));

  // By hour of day
  const hourMap = {};
  for (let h = 0; h < 24; h++) hourMap[h] = 0;
  alerts.forEach(a => {
    const d = parseAlertDate(a);
    hourMap[d.getHours()] += 1;
  });
  const byHour = Object.entries(hourMap)
    .map(([hour, count]) => ({ hour: parseInt(hour), label: `${hour}:00`, count }))
    .sort((a, b) => a.hour - b.hour);

  // By day of week
  const dowNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const dowMap = {};
  for (let d = 0; d < 7; d++) dowMap[d] = 0;
  alerts.forEach(a => {
    const d = parseAlertDate(a);
    dowMap[d.getDay()] += 1;
  });
  const byDayOfWeek = Object.entries(dowMap)
    .map(([day, count]) => ({ day: parseInt(day), label: dowNames[parseInt(day)], count }))
    .sort((a, b) => a.day - b.day);

  // Recent alerts
  const recentAlerts = alerts.slice(0, 20);

  return {
    totalAlerts,
    totalDrills,
    byCity,
    byZone,
    byThreat,
    byMonth,
    byDay,
    byHour,
    byDayOfWeek,
    recentAlerts,
    dateRange: { start, end },
  };
}
