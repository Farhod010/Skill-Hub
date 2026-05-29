(function () {
    const actionModalEl = document.getElementById("adminActionModal");
    const actionFrame = document.querySelector("[data-admin-modal-frame]");
    const actionTitle = document.getElementById("adminActionModalLabel");
    const deleteModalEl = document.getElementById("deleteConfirmModal");
    const deleteForm = document.querySelector("[data-delete-form]");
    const deleteLabel = document.querySelector("[data-delete-label]");

    const withEmbedParam = (url) => {
        try {
            const resolved = new URL(url, window.location.origin);
            resolved.searchParams.set("embed", "1");
            return resolved.toString();
        } catch (error) {
            return url.includes("?") ? `${url}&embed=1` : `${url}?embed=1`;
        }
    };

    if (actionModalEl && actionFrame && window.bootstrap) {
        const actionModal = bootstrap.Modal.getOrCreateInstance(actionModalEl);

        document.addEventListener("click", (event) => {
            const trigger = event.target.closest("[data-admin-modal-url]");
            if (!trigger) {
                return;
            }

            event.preventDefault();
            const rawUrl = trigger.getAttribute("data-admin-modal-url");
            if (!rawUrl) {
                return;
            }

            actionTitle.textContent = trigger.getAttribute("data-admin-modal-title") || "Manage item";
            actionFrame.src = withEmbedParam(rawUrl);
            actionModal.show();
        });

        actionModalEl.addEventListener("hidden.bs.modal", () => {
            actionFrame.src = "about:blank";
        });
    }

    if (deleteModalEl && deleteForm && deleteLabel && window.bootstrap) {
        const deleteModal = bootstrap.Modal.getOrCreateInstance(deleteModalEl);

        document.addEventListener("click", (event) => {
            const trigger = event.target.closest("[data-delete-url]");
            if (!trigger) {
                return;
            }

            event.preventDefault();
            deleteForm.action = trigger.getAttribute("data-delete-url");
            deleteLabel.textContent = trigger.getAttribute("data-delete-label") || "This action cannot be undone.";
            deleteModal.show();
        });
    }

    document.addEventListener("click", (event) => {
        const toggle = event.target.closest("[data-password-toggle]");
        if (!toggle) {
            return;
        }

        const targetId = toggle.getAttribute("data-password-target");
        const input = targetId ? document.getElementById(targetId) : null;
        if (!input) {
            return;
        }

        const isPassword = input.getAttribute("type") === "password";
        input.setAttribute("type", isPassword ? "text" : "password");
        const icon = toggle.querySelector("i");
        if (icon) {
            icon.className = isPassword ? "bi bi-eye-slash" : "bi bi-eye";
        }
    });

    document.addEventListener("click", (event) => {
        const trigger = event.target.closest("[data-export-table]");
        if (!trigger) {
            return;
        }

        event.preventDefault();
        const table = document.querySelector(trigger.getAttribute("data-export-table"));
        if (!table) {
            return;
        }

        const rows = Array.from(table.querySelectorAll("tr"));
        const csvRows = rows.map((row) => {
            const cells = Array.from(row.querySelectorAll("th, td"));
            return cells
                .map((cell) => {
                    const text = cell.innerText.replace(/\s+/g, " ").trim();
                    return `"${text.replace(/"/g, '""')}"`;
                })
                .join(",");
        });

        const blob = new Blob([csvRows.join("\n")], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.href = url;
        link.download = `${trigger.getAttribute("data-export-name") || "export"}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    });
})();
