export async function getUserLocationName(): Promise<string> {
  if (typeof window === 'undefined' || !('navigator' in window)) return '';

  const getPosition = () =>
    new Promise<GeolocationPosition>((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'));
        return;
      }
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: false,
        timeout: 5000,
        maximumAge: 60_000,
      });
    });

  try {
    const pos = await getPosition();
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;

    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`;
    const res = await fetch(url, {
      headers: {
        'Accept': 'application/json',
      },
    });
    if (!res.ok) return '';
    const data = await res.json();
    const address = data?.address || {};
    const city = address.city || address.town || address.village || address.hamlet || '';
    const state = address.state || '';
    const country = address.country || '';
    const parts = [city || state, country].filter(Boolean);
    return parts.join(', ');
  } catch {
    return '';
  }
}
