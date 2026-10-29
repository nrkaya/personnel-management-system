// All page behaviour lives here: the Content-Security-Policy forbids inline
// scripts and on* attributes, so templates only declare data-* hooks.
//   data-modal-open="id"   opens a modal; data-modal-action / data-modal-values
//                          (JSON) fill its form, [data-bind] shows values as text
//   data-modal-close       closes the surrounding modal
//   data-confirm="text"    asks before a form is submitted
//   data-autosubmit        submits the form when a select changes
//   data-print             prints the page

function openModal(id, opener) {
    const overlay = document.getElementById(id);
    if (!overlay) {
        return;
    }
    const form = overlay.querySelector("form");
    if (form && opener && opener.dataset.modalAction) {
        form.action = opener.dataset.modalAction;
    }
    if (opener && opener.dataset.modalValues) {
        const values = JSON.parse(opener.dataset.modalValues);
        Object.entries(values).forEach(([name, value]) => {
            overlay.querySelectorAll(`[data-bind="${name}"]`).forEach((el) => {
                el.textContent = value;
            });
            const field = form && form.elements.namedItem(name);
            if (!field) {
                return;
            }
            if (field.type === "checkbox") {
                field.checked = Boolean(value);
            } else {
                field.value = value === null || value === undefined ? "" : value;
            }
        });
        // Fields an admin may not change on their own account.
        overlay.querySelectorAll("[data-lockable]").forEach((el) => {
            el.disabled = Boolean(values._locked);
        });
    }
    overlay.classList.add("active");
    const firstInput = overlay.querySelector("input:not([type=hidden]):not([disabled]), select, textarea");
    if (firstInput) {
        firstInput.focus();
    }
}

function closeModal(overlay) {
    if (overlay) {
        overlay.classList.remove("active");
    }
}

function renderDepartmentChart() {
    const dataBlock = document.getElementById("deptChartData");
    const canvas = document.getElementById("deptChart");
    if (!dataBlock || !canvas || !window.Chart) {
        return;
    }
    const chartData = JSON.parse(dataBlock.textContent);
    new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: chartData.labels,
            datasets: [{
                label: chartData.label,
                data: chartData.counts,
                backgroundColor: [
                    "rgba(59, 130, 246, 0.85)",
                    "rgba(139, 92, 246, 0.85)",
                    "rgba(236, 72, 153, 0.85)",
                    "rgba(16, 185, 129, 0.85)",
                    "rgba(245, 158, 11, 0.85)",
                    "rgba(14, 165, 233, 0.85)"
                ],
                borderColor: "rgba(255, 255, 255, 0.1)",
                borderWidth: 2,
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { color: "#a1a1aa", font: { family: "Inter", size: 12 } }
                }
            },
            cutout: "65%"
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    // Initialize Lucide icons
    if (window.lucide) {
        lucide.createIcons();
    }

    renderDepartmentChart();

    document.addEventListener("click", (event) => {
        const opener = event.target.closest("[data-modal-open]");
        if (opener) {
            openModal(opener.dataset.modalOpen, opener);
            return;
        }
        const closer = event.target.closest("[data-modal-close]");
        if (closer) {
            closeModal(closer.closest(".modal-overlay"));
            return;
        }
        if (event.target.classList.contains("modal-overlay")) {
            closeModal(event.target);
            return;
        }
        if (event.target.closest("[data-print]")) {
            window.print();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            document.querySelectorAll(".modal-overlay.active").forEach(closeModal);
        }
    });

    document.addEventListener("submit", (event) => {
        const message = event.target.dataset.confirm;
        if (message && !window.confirm(message)) {
            event.preventDefault();
        }
    });

    document.addEventListener("change", (event) => {
        if (event.target.matches("select[data-autosubmit]") && event.target.form) {
            event.target.form.requestSubmit();
        }
    });

    // Deep link from the dashboard's "new personnel" button.
    if (window.location.hash === "#yeni-personel") {
        openModal("personnelModal");
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
