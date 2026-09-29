// mostly AI
const CACHE_NAME = 'chronis';
const SCHEDULE_API = '/api/v2/schedule/today';
const SCHEDULE_DATE_KEY = 'cachedate';
let scheduleUpdatePromise = null;

function getTodayDateString() {
    const today = new Date();
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
}

async function isScheduleCacheStale() {
    const cache = await caches.open(CACHE_NAME);
    const dateResponse = await cache.match(SCHEDULE_DATE_KEY);
    if (!dateResponse) {
        return true; // No date cached, considered stale
    }
    const cachedDate = await dateResponse.text();
    const today = getTodayDateString();
    return cachedDate !== today;
}

self.addEventListener('install', (event) => {
    self.skipWaiting();
    event.waitUntil(cacheConfig());
});

self.addEventListener('activate', (event) => {
    self.skipWaiting();
    event.waitUntil(updateScheduleIfStale());
});

self.addEventListener('fetch', async (event) => {
    const url = new URL(event.request.url);

    // Cache the schedule API specifically
    if (url.pathname === SCHEDULE_API) {
        event.respondWith(
            (async () => {
                await updateScheduleIfStale();
                const cache = await caches.open(CACHE_NAME);
                const cachedResponse = await cache.match(SCHEDULE_API);
                if (cachedResponse) {
                    return cachedResponse;
                }
                return fetchAndCacheSchedule(true);
            })()
        );
        return;
    }

    if (event.request.mode === 'navigate') {
        event.respondWith(
            (async () => {
                // Check if schedule cache is stale and refetch if needed
                if (await isScheduleCacheStale()) {
                    await updateScheduleIfStale();
                }
                
                return fetch(event.request).then(async (response) => {
                    if (response.status > 500) {
                        const nconfig = await caches.open(CACHE_NAME).then(cache => cache.match('/api/v2/chronisconfig')).then(resp => resp ? resp.json() : null);
                        if (new URL(event.request.url).pathname.startsWith('/canvas') && nconfig && nconfig.canvas_url) {
                            return Response.redirect(nconfig.canvas_url, 302);
                        }
                        return new Response(await getOfflinePageHTML("Chronis is offline: " + response.status), {
                            headers: { 'Content-Type': 'text/html' }
                        });
                    }
                    if (response.status === 500) {
                        const clonedResponse = response.clone();
                        try {
                            const text = await clonedResponse.text();
                            if (text.includes("https://www.cloudflare.com/5xx-error-landing")) {
                                const nconfig = await caches.open(CACHE_NAME).then(cache => cache.match('/api/v2/chronisconfig')).then(resp => resp ? resp.json() : null);
                                if (new URL(event.request.url).pathname.startsWith('/canvas') && nconfig && nconfig.canvas_url) {
                                    return Response.redirect(nconfig.canvas_url, 302);
                                }
                                return new Response(await getOfflinePageHTML("Chronis is offline: 500"), {
                                    headers: { 'Content-Type': 'text/html' }
                                });
                            }
                        } catch (e) {}
                    }
                    return response;
                }).catch(async (e) => {
                    console.error("Page fetch failed: ", e);
                    return new Response(await getOfflinePageHTML("Chronis cannot be reached: " + e), {
                        headers: { 'Content-Type': 'text/html' }
                    });
                });
            })()
        );
        return;
    }
});

async function getCurrentPeriod() {
    const cache = await caches.open(CACHE_NAME);
    const response = await cache.match(SCHEDULE_API);
    if (!response) {
        return null;
    }
    const data = await response.json();
    const schedule = data.schedule || (data.data && data.data.schedule);
    if (!schedule) {
        return null;
    }
    const now = Date.now() / 1000;
    for (const entry of schedule) {
        if (now >= entry.start && now < entry.end) {
            return entry;
        }
    }
    return null;
}

async function fetchAndCacheSchedule(fallbackToCache = false) {
    try {
        const response = await fetch(SCHEDULE_API, { credentials: 'include' });
        if (response.status === 200) {
            const cache = await caches.open(CACHE_NAME);
            await cache.put(SCHEDULE_API, response.clone());
            await cache.put(SCHEDULE_DATE_KEY, new Response(getTodayDateString()));
            return response;
        }
        if (fallbackToCache) {
            return (await caches.match(SCHEDULE_API)) || response;
        }
        return response;
    } catch (error) {
        const cachedResponse = await caches.match(SCHEDULE_API);
        if (cachedResponse) {
            return cachedResponse;
        }
        throw error;
    }
}

async function updateScheduleIfStale() {
    if (!(await isScheduleCacheStale())) {
        return;
    }
    if (!scheduleUpdatePromise) {
        scheduleUpdatePromise = fetchAndCacheSchedule()
            .catch(() => undefined)
            .finally(() => {
                scheduleUpdatePromise = null;
            });
    }
    await scheduleUpdatePromise;
}

async function cacheConfig() {
    try {
        const response = await fetch('/api/v2/chronisconfig');
        if (response.status === 200) {
            const cache = await caches.open(CACHE_NAME);
            await cache.put('/api/v2/chronisconfig', response);
        }
    } catch (error) {
        console.error("Config fetch failed: ", error);
    }
}

async function getOfflinePageHTML(r="You are offline") {
    const config = await caches.open(CACHE_NAME)
        .then(cache => cache.match('/api/v2/chronisconfig'))
        .then(resp => resp ? resp.json() : null);
    const colorHue = (config && config.color_hue) ? config.color_hue : 155;
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
            background-color: hsl(${colorHue}, 8%, 5%);
            color: hsl(${colorHue}, 100%, 88%);
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
<h3 id="periodtime"></h3>
<h1 id="timeleft"></h1>
</div>
<p id="statusmsg" style="position:absolute; bottom: 10px; right: 20px; text-align: right;">${r}<span id="guessmsg"><br>The timer shown is a best guess.</span></p>
</body>
<script>
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
    async function updateTimer() {
        try {
            const cache = await caches.open('${CACHE_NAME}');
            const response = await cache.match('${SCHEDULE_API}');
            if (!response) {
                document.getElementById('timeleft').innerText = "";
                document.getElementById('periodtime').innerText = "";
                const guessMsg = document.getElementById('guessmsg');
                if (guessMsg) {
                    guessMsg.remove();
                }
                return;
            }
            const data = await response.json();
            const schedule = data.schedule || (data.data && data.data.schedule);
            if (!schedule) {
                document.getElementById('timeleft').innerText = "";
                document.getElementById('periodtime').innerText = "";
                const guessMsg = document.getElementById('guessmsg');
                if (guessMsg) {
                    guessMsg.remove();
                }
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
                const guessMsg = document.getElementById('guessmsg');
                if (guessMsg) {
                    guessMsg.remove();
                }
            }
        } catch (e) {
            console.error(e);
            document.getElementById('timeleft').innerText = "Error loading cached data.";
        }
    }
    updateTimer();
    setInterval(updateTimer, 1000);
</script>
</html>`;
}
