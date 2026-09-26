(function () {
    const STORAGE_KEY = "studymate_triggered_alarms_v1";

    function getTriggered() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
        } catch (e) {
            return {};
        }
    }

    function setTriggered(data) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    }

    function requestPermission() {
        if ("Notification" in window && Notification.permission === "default") {
            Notification.requestPermission().catch(function () {});
        }
    }

    function playAlarm() {
        try {
            const AudioContext =
                window.AudioContext || window.webkitAudioContext;

            if (!AudioContext) return;

            const ctx = new AudioContext();
            const now = ctx.currentTime;

            [0, 0.25, 0.5, 0.75].forEach(function (offset, i) {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();

                osc.type = "sine";
                osc.frequency.value = i % 2 === 0 ? 880 : 660;

                gain.gain.setValueAtTime(
                    0.001,
                    now + offset
                );

                gain.gain.exponentialRampToValueAtTime(
                    0.25,
                    now + offset + 0.03
                );

                gain.gain.exponentialRampToValueAtTime(
                    0.001,
                    now + offset + 0.20
                );

                osc.connect(gain);
                gain.connect(ctx.destination);

                osc.start(now + offset);
                osc.stop(now + offset + 0.22);
            });
        } catch (e) {
            console.log("Alarm sound error:", e);
        }
    }

    function showReminder(alarm) {
        playAlarm();

        // Browser notification
        if (
            "Notification" in window &&
            Notification.permission === "granted"
        ) {
            try {
                new Notification(
                    alarm.title || "StudyMate Reminder",
                    {
                        body:
                            alarm.message ||
                            "Your reminder is due now.",
                        icon: "/static/bg.jpg"
                    }
                );
            } catch (e) {
                console.log("Notification error:", e);
            }
        }

        // Visible reminder popup
        const box = document.createElement("div");

        box.style.cssText =
            "position:fixed;" +
            "right:20px;" +
            "bottom:20px;" +
            "z-index:99999;" +
            "max-width:360px;" +
            "background:#fff;" +
            "padding:18px 20px;" +
            "border-radius:16px;" +
            "box-shadow:0 8px 30px rgba(0,0,0,.25);" +
            "border-left:6px solid #f9c80e;" +
            "font-family:Arial,sans-serif;" +
            "color:#26354a;";

        box.innerHTML =
            "<strong style='font-size:18px;'>" +
            (alarm.title || "StudyMate Reminder") +
            "</strong>" +

            "<div style='margin-top:7px;'>" +
            (alarm.message ||
                "Your reminder is due now.") +
            "</div>" +

            "<button " +
            "style='margin-top:12px;" +
            "border:0;" +
            "border-radius:8px;" +
            "padding:8px 12px;" +
            "background:#0a3472;" +
            "color:white;" +
            "cursor:pointer;'>" +
            "Dismiss" +
            "</button>";

        box.querySelector("button").onclick =
            function () {
                box.remove();
            };

        document.body.appendChild(box);

        // Automatically remove after 20 seconds
        setTimeout(function () {
            if (box.isConnected) {
                box.remove();
            }
        }, 20000);
    }

    async function checkAlarms() {
        try {
            const response = await fetch(
                "/api/alarms",
                {
                    cache: "no-store"
                }
            );

            if (!response.ok) return;

            const data = await response.json();

            const now = new Date();
            const triggered = getTriggered();

            (data.alarms || []).forEach(function (alarm) {

                if (!alarm.date || !alarm.time) {
                    return;
                }

                const target = new Date(
                    alarm.date +
                    "T" +
                    alarm.time +
                    ":00"
                );

                const key =
                    alarm.id +
                    "|" +
                    alarm.date +
                    "|" +
                    alarm.time;

                const diff =
                    now.getTime() -
                    target.getTime();

                /*
                 * Alarm window:
                 * from the exact alarm time
                 * up to 2 minutes after.
                 */
                if (
                    diff >= 0 &&
                    diff <= 120000 &&
                    !triggered[key]
                ) {
                    triggered[key] = Date.now();

                    showReminder(alarm);
                }
            });

            // Remove old alarm records after 7 days
            const cutoff =
                Date.now() -
                (7 * 24 * 60 * 60 * 1000);

            Object.keys(triggered).forEach(
                function (key) {
                    if (triggered[key] < cutoff) {
                        delete triggered[key];
                    }
                }
            );

            setTriggered(triggered);

        } catch (e) {
            console.log(
                "StudyMate alarm check error:",
                e
            );
        }
    }

    /*
     * Ask permission when the user first clicks
     * anywhere on the page.
     */
    document.addEventListener(
        "click",
        requestPermission,
        { once: true }
    );

    /*
     * Check immediately.
     */
    checkAlarms();

    /*
     * Check every 15 seconds.
     */
    setInterval(
        checkAlarms,
        15000
    );

})();