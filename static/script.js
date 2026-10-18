/* =========================================================
   MINDBRIDGE — GLOBAL JAVASCRIPT
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       MOBILE NAVIGATION
       ===================================================== */

    const menuButton = document.getElementById("mobileMenuBtn");
    const mobileNav = document.getElementById("mobileNav");

    if (menuButton && mobileNav) {

        menuButton.addEventListener("click", () => {
            mobileNav.classList.toggle("active");
        });

        // Close mobile menu after clicking a link
        const mobileLinks = mobileNav.querySelectorAll("a");

        mobileLinks.forEach(link => {
            link.addEventListener("click", () => {
                mobileNav.classList.remove("active");
            });
        });
    }


    /* =====================================================
       CLOSE MOBILE MENU WHEN CLICKING OUTSIDE
       ===================================================== */

    document.addEventListener("click", (event) => {

        if (!menuButton || !mobileNav) return;

        const clickedInsideMenu =
            mobileNav.contains(event.target);

        const clickedButton =
            menuButton.contains(event.target);

        if (
            !clickedInsideMenu &&
            !clickedButton
        ) {
            mobileNav.classList.remove("active");
        }
    });


    /* =====================================================
       SCROLL REVEAL ANIMATION
       ===================================================== */

    const revealElements =
        document.querySelectorAll(
            ".reveal, .feature-card, .step-card, .team-card"
        );

    if ("IntersectionObserver" in window) {

        const observer =
            new IntersectionObserver(
                (entries, observer) => {

                    entries.forEach(entry => {

                        if (entry.isIntersecting) {

                            entry.target.classList.add(
                                "visible"
                            );

                            observer.unobserve(
                                entry.target
                            );
                        }

                    });

                },
                {
                    threshold: 0.12
                }
            );

        revealElements.forEach(element => {

            element.classList.add("reveal");

            observer.observe(element);

        });

    } else {

        revealElements.forEach(element => {
            element.classList.add("visible");
        });

    }


    /* =====================================================
       SMOOTH SCROLL FOR ANCHOR LINKS
       ===================================================== */

    document
        .querySelectorAll('a[href^="#"]')
        .forEach(anchor => {

            anchor.addEventListener("click", event => {

                const targetId =
                    anchor.getAttribute("href");

                if (
                    !targetId ||
                    targetId === "#"
                ) {
                    return;
                }

                const target =
                    document.querySelector(targetId);

                if (!target) return;

                event.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            });

        });


    /* =====================================================
       FLASH MESSAGE AUTO DISMISS
       ===================================================== */

    const flashMessages =
        document.querySelectorAll(
            ".flash-message"
        );

    flashMessages.forEach(message => {

        setTimeout(() => {

            message.style.opacity = "0";
            message.style.transform =
                "translateX(20px)";

            message.style.transition =
                "opacity 0.3s ease, transform 0.3s ease";

            setTimeout(() => {
                message.remove();
            }, 300);

        }, 5000);

    });


    /* =====================================================
       BUTTON LOADING STATE
       ===================================================== */

    const loadingButtons =
        document.querySelectorAll(
            "[data-loading]"
        );

    loadingButtons.forEach(button => {

        button.addEventListener("click", () => {

            if (button.dataset.loading === "true") {

                button.disabled = true;

                const originalText =
                    button.innerHTML;

                button.dataset.originalText =
                    originalText;

                button.innerHTML =
                    `
                    <span class="button-spinner"></span>
                    Please wait...
                    `;

            }

        });

    });


    /* =====================================================
       NUMBER INPUT VALIDATION
       ===================================================== */

    const numberInputs =
        document.querySelectorAll(
            'input[type="number"]'
        );

    numberInputs.forEach(input => {

        input.addEventListener("input", () => {

            const min =
                input.getAttribute("min");

            const max =
                input.getAttribute("max");

            let value =
                parseFloat(input.value);

            if (Number.isNaN(value)) return;

            if (
                min !== null &&
                value < Number(min)
            ) {
                input.value = min;
            }

            if (
                max !== null &&
                value > Number(max)
            ) {
                input.value = max;
            }

        });

    });


    /* =====================================================
       PASSWORD VISIBILITY TOGGLE
       ===================================================== */

    const passwordToggles =
        document.querySelectorAll(
            "[data-password-toggle]"
        );

    passwordToggles.forEach(toggle => {

        toggle.addEventListener("click", () => {

            const targetId =
                toggle.dataset.passwordToggle;

            const passwordInput =
                document.getElementById(targetId);

            if (!passwordInput) return;

            if (
                passwordInput.type === "password"
            ) {

                passwordInput.type = "text";

                toggle.textContent = "Hide";

            } else {

                passwordInput.type = "password";

                toggle.textContent = "Show";

            }

        });

    });


    /* =====================================================
       PREVENT DOUBLE FORM SUBMISSION
       ===================================================== */

    const forms =
        document.querySelectorAll("form");

    forms.forEach(form => {

        form.addEventListener("submit", event => {

            if (form.dataset.submitted === "true") {

                event.preventDefault();

                return;

            }

            form.dataset.submitted = "true";

        });

    });


    /* =====================================================
       CURRENT YEAR
       ===================================================== */

    const yearElements =
        document.querySelectorAll(
            "[data-current-year]"
        );

    yearElements.forEach(element => {

        element.textContent =
            new Date().getFullYear();

    });

});