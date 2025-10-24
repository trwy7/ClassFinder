// check for <meta name="endtime" content="<timestamp>">
const metaEndtime = document.querySelector('meta[name="endtime"]');
if (metaEndtime) {
    if (metaEndtime.content === "") {
        console.log("Meta endtime content is empty.");
        localStorage.removeItem("currentperiod_endtime");
    } else {
        const endtime = new Date(Number(metaEndtime.content) * 1000).getTime();
        localStorage.setItem("currentperiod_endtime", endtime);
        console.log("Saved currentperiod_endtime to localStorage:", endtime);
    }
} else {
    console.log("Checking localStorage for currentperiod_endtime");
    const endtime = localStorage.getItem("currentperiod_endtime");
    if (endtime) {
        console.log("Found currentperiod_endtime in localStorage:", endtime);
    } else {
        console.log("No currentperiod_endtime found in localStorage.");
    }
}

// check for #timertext

const timerTextElement = document.getElementById('timertext');
if (timerTextElement) {
    if (!localStorage.getItem("currentperiod_endtime")) {
        timerTextElement.parentElement.remove();
    }
    const endtime = parseInt(localStorage.getItem("currentperiod_endtime"));
    function updateTimer() {
        const now = new Date().getTime();
        const distance = endtime - now;
        if (distance < 0 || isNaN(distance)) {
            timerTextElement.innerHTML = "Timer";
            clearInterval(timerInterval);
            localStorage.removeItem("currentperiod_endtime");
            return;
        }
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        timerTextElement.innerHTML = 
            (hours > 0 ? hours + "h " : "") + 
            (minutes > 0 ? minutes + "m " : "") + 
            seconds + "s";
    }
    const timerInterval = setInterval(updateTimer, 1000);
    updateTimer(); // initial call
}