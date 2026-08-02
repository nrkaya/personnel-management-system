document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide icons
    if (window.lucide) {
        lucide.createIcons();
    }

    // Client-side quick search filtering
    const liveSearchInput = document.getElementById("liveSearchInput");
    const personelRows = document.querySelectorAll(".personel-row");

    if (liveSearchInput && personelRows.length > 0) {
        liveSearchInput.addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase().trim();
            personelRows.forEach((row) => {
                const text = row.innerText.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        });
    }

    // Auto-dismiss toast notifications
    const flashes = document.querySelectorAll(".flash-message");
    flashes.forEach((flash) => {
        setTimeout(() => {
            flash.style.opacity = "0";
            flash.style.transform = "translateX(100%)";
            flash.style.transition = "all 0.4s cubic-bezier(0.16, 1, 0.3, 1)";
            setTimeout(() => flash.remove(), 400);
        }, 4500);
    });
});
