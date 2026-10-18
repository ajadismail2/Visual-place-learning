/* Change target.json to retarget printed QR codes. No query-string redirects. */
(async () => {
  const status = document.getElementById('status');
  const link = document.getElementById('destination');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch('target.json', {cache: 'no-store', signal: controller.signal});
    if (!response.ok) throw new Error('Destination unavailable');
    const config = await response.json();
    if (typeof config.url !== 'string' || !config.url.trim()) throw new Error('Missing destination');
    const destination = new URL(config.url, location.href);
    const normalized = url => url.origin + url.pathname.replace(/(?:index\.html)?\/$|index\.html$/, '').replace(/\/$/, '');
    if (destination.protocol !== 'https:' || destination.username || destination.password || normalized(destination) === normalized(new URL(location.href))) {
      throw new Error('Invalid destination');
    }
    link.href = destination.href;
    location.replace(destination.href);
  } catch (_) {
    status.textContent = 'The redirect is unavailable. Use the website link below.';
  } finally {
    clearTimeout(timeout);
  }
})();
