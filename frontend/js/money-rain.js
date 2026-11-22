// Money rain: coins and bills fall from the top of the screen to celebrate reaching the savings goal.
// Decorative only. It never shows or changes an amount; the symbol follows the user's ₪/$ choice (D9).

const SYMBOLS = { ILS: "₪", USD: "$" };
const ACHIEVED = "already_achieved"; // status name from the engine (assess() in engine.py)

/**
 * Celebrate only on the moment the goal becomes achieved, not on every page load
 * while it stays achieved.
 */
export function shouldCelebrate(previousStatus, newStatus) {
  return newStatus === ACHIEVED && previousStatus !== ACHIEVED;
}

function prefersReducedMotion() {
  return typeof window.matchMedia === "function"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function makePiece(symbol, isBill) {
  const el = document.createElement("span");
  el.textContent = symbol;
  const size = isBill ? 0 : 28 + Math.random() * 18;
  Object.assign(el.style, {
    position: "absolute",
    top: "-60px",
    left: `${Math.random() * 100}%`,
    display: "grid",
    placeItems: "center",
    fontFamily: "Rubik, Arial, sans-serif",
    fontWeight: "700",
    lineHeight: "1",
    userSelect: "none",
    willChange: "transform",
  });
  if (isBill) {
    Object.assign(el.style, {
      width: "64px", height: "34px", borderRadius: "4px", fontSize: "18px",
      background: "#9FD6B4", color: "#16503F", border: "2px solid #1F6B57",
    });
  } else {
    Object.assign(el.style, {
      width: `${size}px`, height: `${size}px`, borderRadius: "50%", fontSize: `${size * 0.55}px`,
      background: "#F2C14E", color: "#7A4700", border: "2px solid #C8901B",
    });
  }
  return el;
}

/**
 * Start the money rain. Returns a Promise that resolves when it has finished and been removed.
 * @param {{currency?: "ILS"|"USD", pieces?: number, durationMs?: number}} options
 */
export function moneyRain({ currency = "ILS", pieces = 60, durationMs = 3500 } = {}) {
  const symbol = SYMBOLS[currency];
  if (!symbol) throw new Error(`Unsupported currency: ${currency}`);
  if (prefersReducedMotion()) return Promise.resolve(); // no falling motion; the screen's own message still shows

  const layer = document.createElement("div");
  layer.setAttribute("aria-hidden", "true"); // decoration only; screen readers get the screen's text
  Object.assign(layer.style, {
    position: "fixed", inset: "0", overflow: "hidden", pointerEvents: "none", zIndex: "1000",
  });
  document.body.appendChild(layer);

  const height = window.innerHeight + 120;
  const animations = [];
  for (let i = 0; i < pieces; i++) {
    const piece = makePiece(symbol, Math.random() < 0.3);
    layer.appendChild(piece);
    const spin = (Math.random() - 0.5) * 720;
    const drift = (Math.random() - 0.5) * 120;
    const fall = durationMs * (0.6 + Math.random() * 0.4);
    const anim = piece.animate(
      [
        { transform: "translate(0, 0) rotate(0deg)", opacity: 1 },
        { transform: `translate(${drift}px, ${height}px) rotate(${spin}deg)`, opacity: 0.9 },
      ],
      { duration: fall, delay: Math.random() * (durationMs - fall), easing: "cubic-bezier(.3,.6,.6,1)", fill: "forwards" },
    );
    animations.push(anim.finished);
  }

  return Promise.allSettled(animations).then(() => layer.remove());
}
