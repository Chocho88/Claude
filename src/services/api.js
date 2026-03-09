const OREF_HISTORY_URL = '/api/oref/history';
const OREF_ALARMS_HISTORY_URL = '/api/oref/alarms-history';

export async function fetchAlertHistory() {
  try {
    const res = await fetch(OREF_HISTORY_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Failed to fetch live alert history, using sample data:', err.message);
    return null;
  }
}

export async function fetchAlarmsHistory(lang = 'he') {
  try {
    const res = await fetch(`${OREF_ALARMS_HISTORY_URL}?lang=${lang}&mode=1`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Failed to fetch alarms history, using sample data:', err.message);
    return null;
  }
}
