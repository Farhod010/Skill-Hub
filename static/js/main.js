document.addEventListener("DOMContentLoaded", () => {
    const root = document.documentElement;
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)");
    const storedTheme = window.localStorage.getItem("theme");

    const applyTheme = (theme) => {
        root.setAttribute("data-bs-theme", theme);
        window.localStorage.setItem("theme", theme);
    };

    if (storedTheme) {
        applyTheme(storedTheme);
    } else {
        applyTheme(prefersDark.matches ? "dark" : "light");
    }

    prefersDark.addEventListener("change", (event) => {
        if (!window.localStorage.getItem("theme")) {
            applyTheme(event.matches ? "dark" : "light");
        }
    });

    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            const nextTheme = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
            applyTheme(nextTheme);
        });
    });

    const enhanceForms = () => {
        document.querySelectorAll("input, select, textarea").forEach((field) => {
            if (field.classList.contains("form-control") || field.classList.contains("form-select") || field.classList.contains("form-check-input")) {
                return;
            }

            const tagName = field.tagName.toLowerCase();
            const type = (field.getAttribute("type") || "").toLowerCase();

            if (type === "hidden" || type === "submit" || type === "button") {
                return;
            }

            if (tagName === "select") {
                field.classList.add("form-select");
            } else if (type === "checkbox" || type === "radio") {
                field.classList.add("form-check-input");
            } else if (type === "file") {
                field.classList.add("form-control");
            } else {
                field.classList.add("form-control");
            }
        });

        document.querySelectorAll(".checkbox-field").forEach((field) => {
            field.classList.add("form-check", "ps-0");
        });
    };

    const activateLinks = () => {
        document.querySelectorAll(".nav-link-premium, .sidebar-link, .dashboard-anchor").forEach((link) => {
            const href = link.getAttribute("href");
            if (!href) {
                return;
            }

            const url = new URL(href, window.location.origin);
            const currentPath = window.location.pathname;
            const samePath = url.pathname === currentPath;
            const sameHash = !url.hash || url.hash === window.location.hash;

            if (samePath && sameHash) {
                link.classList.add("active");
            }
        });
    };

    const closeOffcanvasOnClick = () => {
        const offcanvasElement = document.getElementById("mainNavbar");
        if (!offcanvasElement || typeof bootstrap === "undefined") {
            return;
        }

        const offcanvasInstance = bootstrap.Offcanvas.getOrCreateInstance(offcanvasElement);
        offcanvasElement.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", () => {
                offcanvasInstance.hide();
            });
        });
    };

    const setupPasswordToggles = () => {
        document.querySelectorAll("[data-password-toggle]").forEach((wrap) => {
            const input = wrap.querySelector("input");
            const button = wrap.querySelector("[data-password-toggle-button]");
            if (!input || !button) {
                return;
            }

            button.addEventListener("click", () => {
                const isVisible = input.type === "text";
                input.type = isVisible ? "password" : "text";
                button.innerHTML = isVisible ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
            });
        });
    };

    const animateCounters = () => {
        const counters = document.querySelectorAll("[data-countup]");
        const formatter = (value, decimals) => value.toLocaleString(undefined, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
        });

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                const node = entry.target;
                observer.unobserve(node);
                const target = Number(node.dataset.countup || "0");
                const decimals = Number(node.dataset.countupDecimals || (String(target).includes(".") ? 1 : 0));
                const duration = 1100;
                const start = performance.now();

                const tick = (now) => {
                    const progress = Math.min((now - start) / duration, 1);
                    const eased = 1 - Math.pow(1 - progress, 3);
                    const current = target * eased;
                    node.textContent = formatter(current, decimals);

                    if (progress < 1) {
                        requestAnimationFrame(tick);
                    } else if (target >= 100 && decimals === 0) {
                        node.textContent = `${formatter(target, decimals)}+`;
                    } else {
                        node.textContent = formatter(target, decimals);
                    }
                };

                requestAnimationFrame(tick);
            });
        }, { threshold: 0.35 });

        counters.forEach((counter) => observer.observe(counter));
    };

    const animateProgressBars = () => {
        const bars = document.querySelectorAll("[data-progress] .progress-bar, [data-progress] span");
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                const bar = entry.target;
                observer.unobserve(bar);
                const finalWidth = bar.style.width || bar.getAttribute("aria-valuenow") || "0%";
                bar.dataset.width = finalWidth;
                bar.style.width = "0%";
                requestAnimationFrame(() => {
                    bar.style.width = bar.dataset.width;
                });
            });
        }, { threshold: 0.25 });

        bars.forEach((bar) => observer.observe(bar));
    };

    const smoothAnchors = () => {
        document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
            anchor.addEventListener("click", (event) => {
                const href = anchor.getAttribute("href");
                if (!href || href === "#") {
                    return;
                }

                const target = document.querySelector(href);
                if (!target) {
                    return;
                }

                event.preventDefault();
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            });
        });
    };

    const decorateTables = () => {
        document.querySelectorAll(".data-table").forEach((table) => {
            table.classList.add("table", "table-hover", "align-middle", "mb-0");
        });

        document.querySelectorAll(".table-card").forEach((card) => {
            card.classList.add("table-responsive", "table-premium", "glass-card", "p-0");
        });
    };

    enhanceForms();
    activateLinks();
    closeOffcanvasOnClick();
    setupPasswordToggles();
    animateCounters();
    animateProgressBars();
    smoothAnchors();
    decorateTables();

    const players = document.querySelectorAll("[data-watch-player]");
    players.forEach((player) => {
        const progressUrl = player.dataset.progressUrl;
        const csrfToken = player.dataset.csrfToken;
        const startSeconds = Number(player.dataset.startSeconds || 0);
        let lastSent = -1;

        const seekToSavedPosition = () => {
            if (!Number.isNaN(startSeconds) && startSeconds > 0 && startSeconds < player.duration) {
                player.currentTime = startSeconds;
            }
        };

        const sendProgress = (completed = false, force = false) => {
            if (!progressUrl || !csrfToken) {
                return;
            }

            const watchedSeconds = Math.floor(player.currentTime || 0);
            if (!completed && !force && watchedSeconds === lastSent) {
                return;
            }
            if (!completed && !force && watchedSeconds <= 0) {
                return;
            }

            lastSent = watchedSeconds;
            fetch(progressUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: JSON.stringify({
                    watched_seconds: watchedSeconds,
                    completed,
                }),
            }).catch(() => {});
        };

        player.addEventListener("loadedmetadata", seekToSavedPosition, { once: true });
        player.addEventListener("pause", () => sendProgress(false));
        player.addEventListener("ended", () => sendProgress(true));
        player.addEventListener("timeupdate", () => {
            const watchedSeconds = Math.floor(player.currentTime || 0);
            if (watchedSeconds > 0 && watchedSeconds - lastSent >= 15) {
                sendProgress(false);
            }
        });
        document.addEventListener("visibilitychange", () => {
            if (document.hidden) {
                sendProgress(false, true);
            }
        });
        window.addEventListener("pagehide", () => sendProgress(false, true));
        window.addEventListener("beforeunload", () => sendProgress(false, true));
    });
});
