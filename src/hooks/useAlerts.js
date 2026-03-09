import { useState, useEffect } from 'react';
import { fetchAlarmsHistory } from '../services/api';
import { generateSampleData } from '../services/sampleData';
import { computeStats } from '../utils/stats';

export function useAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isLiveData, setIsLiveData] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await fetchAlarmsHistory('he');
        if (data && Array.isArray(data) && data.length > 0) {
          // Normalize live data
          const normalized = data.map((a, i) => ({
            rid: a.rid || i,
            name: a.data || a.name || '',
            name_en: a.data_en || a.name_en || a.data || '',
            zone: a.zone || '',
            zone_en: a.zone_en || a.zone || '',
            time: a.alertDate || a.time || '',
            datetime: a.alertDate || a.time || '',
            countdown: a.countdown || 0,
            threat: a.category || a.threat || 1,
            threatName: a.category_desc || a.threatName || '',
            threatName_en: a.category_desc_en || a.threatName_en || '',
            isDrill: a.isDrill || false,
          }));
          setAlerts(normalized);
          setStats(computeStats(normalized));
          setIsLiveData(true);
        } else {
          throw new Error('No live data available');
        }
      } catch (err) {
        console.warn('Using sample data:', err.message);
        const sampleAlerts = generateSampleData(2500);
        setAlerts(sampleAlerts);
        setStats(computeStats(sampleAlerts));
        setIsLiveData(false);
        setError('Live API unavailable. Displaying sample data for demonstration.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return { alerts, stats, loading, error, isLiveData };
}
