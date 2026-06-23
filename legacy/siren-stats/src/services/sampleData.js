// Sample alert data based on the Oref alarms-history API format.
// Used as fallback when the live API is unavailable (e.g. outside Israel or CORS blocked).

const cities = [
  'אשקלון', 'שדרות', 'נתיבות', 'אשדוד', 'באר שבע', 'עוטף עזה',
  'קריית גת', 'אופקים', 'נחל עוז', 'כפר עזה', 'ניר עוז', 'רעים',
  'בארי', 'תל אביב', 'חולון', 'בת ים', 'ראשון לציון', 'חיפה',
  'עכו', 'נהריה', 'קריית שמונה', 'מטולה', 'כפר בלום', 'שלומי',
  'צפת', 'טבריה', 'ירושלים', 'מודיעין', 'רמלה', 'לוד',
  'פתח תקווה', 'רמת גן', 'הרצליה', 'נתניה', 'כפר סבא'
];

const citiesEn = [
  'Ashkelon', 'Sderot', 'Netivot', 'Ashdod', 'Beer Sheva', 'Gaza Envelope',
  'Kiryat Gat', 'Ofakim', 'Nahal Oz', 'Kfar Aza', 'Nir Oz', 'Re\'im',
  'Be\'eri', 'Tel Aviv', 'Holon', 'Bat Yam', 'Rishon LeZion', 'Haifa',
  'Acre', 'Nahariya', 'Kiryat Shmona', 'Metula', 'Kfar Blum', 'Shlomi',
  'Safed', 'Tiberias', 'Jerusalem', 'Modi\'in', 'Ramla', 'Lod',
  'Petah Tikva', 'Ramat Gan', 'Herzliya', 'Netanya', 'Kfar Saba'
];

const zones = [
  'שפלת יהודה', 'עוטף עזה', 'מרכז הנגב', 'לכיש', 'דרום הנגב',
  'גוש דן', 'השרון', 'חיפה והקריות', 'גליל עליון', 'גליל תחתון',
  'ירושלים', 'השפלה', 'עמק יזרעאל'
];

const zonesEn = [
  'Judean Lowlands', 'Gaza Envelope', 'Central Negev', 'Lachish', 'Southern Negev',
  'Gush Dan', 'HaSharon', 'Haifa & Krayot', 'Upper Galilee', 'Lower Galilee',
  'Jerusalem', 'Shfela', 'Jezreel Valley'
];

const threatTypes = [
  { id: 1, name: 'ירי רקטות וטילים', nameEn: 'Rockets & Missiles' },
  { id: 2, name: 'חדירת כלי טיס עוין', nameEn: 'Hostile Aircraft Intrusion' },
  { id: 3, name: 'רעידת אדמה', nameEn: 'Earthquake' },
  { id: 4, name: 'חדירת מחבלים', nameEn: 'Terrorist Infiltration' },
  { id: 5, name: 'אירוע חומרים מסוכנים', nameEn: 'Hazardous Materials' },
  { id: 6, name: 'צונאמי', nameEn: 'Tsunami' },
];

function randomDate(startDate, endDate) {
  const start = startDate.getTime();
  const end = endDate.getTime();
  return new Date(start + Math.random() * (end - start));
}

function formatDate(date) {
  const d = date.getDate().toString().padStart(2, '0');
  const m = (date.getMonth() + 1).toString().padStart(2, '0');
  const y = date.getFullYear();
  const h = date.getHours().toString().padStart(2, '0');
  const min = date.getMinutes().toString().padStart(2, '0');
  const s = date.getSeconds().toString().padStart(2, '0');
  return `${d}.${m}.${y} ${h}:${min}:${s}`;
}

export function generateSampleData(count = 2500) {
  const alerts = [];
  const endDate = new Date();
  const startDate = new Date();
  startDate.setFullYear(startDate.getFullYear() - 1);

  // Weight southern cities more heavily for realism
  const weightedCityIndices = [];
  for (let i = 0; i < cities.length; i++) {
    const weight = i < 13 ? 8 : i < 18 ? 3 : 1; // Southern cities appear more
    for (let w = 0; w < weight; w++) {
      weightedCityIndices.push(i);
    }
  }

  for (let i = 0; i < count; i++) {
    const date = randomDate(startDate, endDate);
    const cityIdx = weightedCityIndices[Math.floor(Math.random() * weightedCityIndices.length)];
    const zoneIdx = Math.min(cityIdx % zones.length, zones.length - 1);

    // 85% rockets, 8% aircraft, 4% infiltration, 3% other
    let threatIdx;
    const r = Math.random();
    if (r < 0.85) threatIdx = 0;
    else if (r < 0.93) threatIdx = 1;
    else if (r < 0.97) threatIdx = 3;
    else threatIdx = Math.floor(Math.random() * threatTypes.length);

    const threat = threatTypes[threatIdx];

    alerts.push({
      rid: i + 1,
      name: cities[cityIdx],
      name_en: citiesEn[cityIdx],
      zone: zones[zoneIdx],
      zone_en: zonesEn[zoneIdx],
      time: formatDate(date),
      datetime: date.toISOString(),
      countdown: [15, 30, 45, 60, 90][Math.floor(Math.random() * 5)],
      threat: threat.id,
      threatName: threat.name,
      threatName_en: threat.nameEn,
      isDrill: Math.random() < 0.02,
    });
  }

  // Sort by date descending
  alerts.sort((a, b) => new Date(b.datetime) - new Date(a.datetime));
  return alerts;
}
