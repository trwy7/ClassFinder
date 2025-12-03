// mostly AI
const CACHE_NAME = 'chronis';
const SCHEDULE_API = '/api/v2/schedule/today';

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        Promise.all([
            self.clients.claim(),
            self.registration.navigationPreload ? self.registration.navigationPreload.enable() : Promise.resolve()
        ])
    );
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Cache the schedule API specifically
    if (url.pathname === SCHEDULE_API) {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    // Clone and cache the response if successful
                    if (response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(event.request, responseClone);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // Fallback to cache if offline
                    return caches.match(event.request);
                })
        );
        return;
    }

    // Handle navigation requests for offline page
    if (event.request.mode === 'navigate') {
        event.respondWith(
            (async () => {
                try {
                    const preloadResponse = await event.preloadResponse;
                    let response = preloadResponse;
                    
                    if (!response) {
                        response = await fetch(event.request);
                    }

                    if (response.status > 500) {
                        return new Response(getOfflinePageHTML("Chronis is offline: " + response.status), {
                            headers: { 'Content-Type': 'text/html' }
                        });
                    }
                    if (response.status === 500) {
                        const clonedResponse = response.clone();
                        try {
                            const text = await clonedResponse.text();
                            if (text.includes("https://www.cloudflare.com/5xx-error-landing")) {
                                return new Response(getOfflinePageHTML("Chronis is offline: 500"), {
                                    headers: { 'Content-Type': 'text/html' }
                                });
                            }
                        } catch (e) {
                            // Ignore error reading body
                        }
                    }
                    return response;
                } catch (e) {
                    return new Response(getOfflinePageHTML(), {
                        headers: { 'Content-Type': 'text/html' }
                    });
                }
            })()
        );
        return;
    }
});

function fetchAndCacheSchedule() {
    if (navigator.onLine) {
        fetch(SCHEDULE_API).then(response => {
            if (response.status === 200) {
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(SCHEDULE_API, response);
                });
            }
        });
    }
}

// Poll for schedule updates every 10 minutes while online
setInterval(fetchAndCacheSchedule, 10 * 60 * 1000);
fetchAndCacheSchedule();

function getOfflinePageHTML(r="You are offline") {
    // TODO: Cache the user's color scheme preference and apply it here.
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chronis - Offline</title>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400;1,700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap');
        body {
            background-color: #000;
            color: #c2ffe6;
            font-family: 'Inter', 'Roboto', Arial, sans-serif;
        }
        #maincontent {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }
        #timeleft {
            font-family: 'Space Mono', monospace;
            font-size: 5em;
            font-weight: 700;
            margin: 0;
        }
        #periodtime {
            font-size: 1.5em;
            margin: 0;
        }
    </style>
</head>
<body>
<div id="maincontent">
<h3 id="periodtime">00:00 AM - 00:00 PM</h3>
<h1 id="timeleft">Loading...</h1>
</div>
<p id="statusmsg" style="position:absolute; bottom: 10px; right: 20px; text-align: right;">${r}</p>
</body>
<script>
    async function updateTimer() {
        try {
            const cache = await caches.open('${CACHE_NAME}');
            const response = await cache.match('${SCHEDULE_API}');
            if (!response) {
                document.getElementById('timeleft').innerText = "${r}";
                document.getElementById('periodtime').innerText = "";
                return;
            }
            const data = await response.json();
            const schedule = data.schedule || (data.data && data.data.schedule);
            if (!schedule) {
                document.getElementById('timeleft').innerText = "${r}";
                document.getElementById('periodtime').innerText = "";
                return;
            }
            const now = Date.now() / 1000;
            let currentPeriod = null;

            // Find current period
            for (const entry of schedule) {
                if (now >= entry.start && now < entry.end) {
                    currentPeriod = entry;
                    break;
                }
            }

            if (currentPeriod) {
                const timeLeft = currentPeriod.end - now;
                if (timeLeft < 0) {
                    document.getElementById('timeleft').innerText = "00:00:00";
                    document.getElementById('periodtime').innerText = "";
                    location.reload();
                    return;
                }
                const hours = Math.floor(timeLeft / 3600);
                const minutes = Math.floor((timeLeft % 3600) / 60);
                const seconds = Math.floor(timeLeft % 60);
                document.getElementById('timeleft').innerText =
                    \`\${hours}:\${minutes.toString().padStart(2, '0')}:\${seconds.toString().padStart(2, '0')}\`;

                const startDate = new Date(currentPeriod.start * 1000);
                const endDate = new Date(currentPeriod.end * 1000);
                let startHours = startDate.getHours();
                const startAmpm = startHours >= 12 ? 'PM' : 'AM';
                startHours = startHours % 12;
                startHours = startHours ? startHours : 12; 
                const startMin = startDate.getMinutes().toString().padStart(2, '0');

                let endHours = endDate.getHours();
                const endAmpm = endHours >= 12 ? 'PM' : 'AM';
                endHours = endHours % 12;
                endHours = endHours ? endHours : 12; 
                const endMin = endDate.getMinutes().toString().padStart(2, '0');

                document.getElementById('periodtime').innerText = 
                    \`\${startHours}:\${startMin} \${startAmpm} - \${endHours}:\${endMin} \${endAmpm}\`;
            } else {
                document.getElementById('timeleft').innerText = "";
                document.getElementById('periodtime').innerText = "";
            }
        } catch (e) {
            console.error(e);
            document.getElementById('timeleft').innerText = "Error loading cached data.";
        }
    }

    setInterval(updateTimer, 1000);
    updateTimer();
    function checkOnlineStatus() {
        fetch('/ping').then((resp) => {
            if (resp && resp.status === 200) {
                location.reload();
            }
        }).catch(() => {});
    }
    setInterval(checkOnlineStatus, 5000);
    window.addEventListener('online', () => {
        console.log("Back online, checking status...");
        checkOnlineStatus();
    });
</script>
</html>`;
}
