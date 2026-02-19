// chat_animations.js
// Handles decorative animations with graceful fallbacks for reduced-motion and slower devices.

(() => {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const lowPowerDevice = (navigator.hardwareConcurrency || 8) <= 4;
  const smallScreen = window.innerWidth < 768;
  const shouldReduceEffects = prefersReducedMotion || lowPowerDevice;

  if (shouldReduceEffects) {
    document.body.classList.add("motion-reduced");
  }

  let vantaEffect = null;

  // Initialize lightweight WebGL background only when motion is allowed.
  if (!shouldReduceEffects && !smallScreen && window.VANTA && window.THREE) {
    vantaEffect = window.VANTA.NET({
      el: "#vanta-bg",
      mouseControls: true,
      touchControls: true,
      gyroControls: false,
      minHeight: 200,
      minWidth: 200,
      color: 0x14b8a6,
      backgroundColor: 0x041c2c,
      points: 9.0,
      maxDistance: 22.0,
      spacing: 18.0,
      showDots: false
    });
  }

  // Gentle mouse-parallax for foreground layers.
  const parallaxLayers = document.querySelectorAll(".parallax-layer");
  if (!shouldReduceEffects && parallaxLayers.length > 0) {
    window.addEventListener(
      "pointermove",
      (event) => {
        const nx = event.clientX / window.innerWidth - 0.5;
        const ny = event.clientY / window.innerHeight - 0.5;

        parallaxLayers.forEach((layer) => {
          const depth = parseFloat(layer.dataset.depth || "0.02");
          const tx = nx * 32 * depth;
          const ty = ny * 20 * depth;
          layer.style.transform = `translate3d(${tx}px, ${ty}px, 0)`;
        });
      },
      { passive: true }
    );
  }

  // Reveal cards/sections when they enter view.
  const revealTargets = document.querySelectorAll(".scroll-reveal");
  if (revealTargets.length > 0) {
    if (shouldReduceEffects || !("IntersectionObserver" in window)) {
      revealTargets.forEach((el) => el.classList.add("is-visible"));
    } else {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.16 }
      );
      revealTargets.forEach((el) => observer.observe(el));
    }
  }

  // Subtle scroll-based robot tilt.
  const robot = document.querySelector(".robot-avatar");
  if (!shouldReduceEffects && robot) {
    window.addEventListener(
      "scroll",
      () => {
        const offset = Math.min(window.scrollY / 24, 10);
        robot.style.transform = `translateY(${-(offset / 2)}px) rotate(${offset / 18}deg)`;
      },
      { passive: true }
    );
  }

  // Clean up WebGL effect on unload.
  window.addEventListener("pagehide", () => {
    if (vantaEffect && typeof vantaEffect.destroy === "function") {
      vantaEffect.destroy();
    }
  });
})();
