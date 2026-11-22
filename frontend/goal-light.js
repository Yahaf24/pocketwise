/*
 * PocketWise goal light (D10). Plain JS, no framework.
 *
 * The light value comes from the engine: goal_light(status) in backend/pocketwise_engine/display.py
 *   "on_track"  -> steady green: the plan reaches the goal by the deadline
 *   "celebrate" -> green flash + "הגעת ליעד!" + fireworks and confetti
 *   "off"       -> neutral (never red: no financial shaming, CLAUDE.md rule 9)
 *
 * Usage:
 *   PocketWiseGoalLight.render(document.getElementById("goal-light"), "on_track");
 *   PocketWiseGoalLight.render(el, "celebrate", { goalKey: "goal-1" }); // celebrates once per goal
 *
 * Display only: it never computes or changes amounts.
 */
(function () {
  "use strict";

  var LABELS = {
    off: "בואו נבדוק יחד את האפשרויות",
    on_track: "בדרך ליעד",
    celebrate: "הגעת ליעד! 🎉"
  };
  var CELEBRATION_MS = 5500;
  var lastLight = new WeakMap();

  function reducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function alreadyCelebrated(goalKey) {
    if (!goalKey) return false;
    try { return localStorage.getItem("pocketwise.celebrated." + goalKey) === "1"; } catch (e) { return false; }
  }

  function markCelebrated(goalKey) {
    if (!goalKey) return;
    try { localStorage.setItem("pocketwise.celebrated." + goalKey, "1"); } catch (e) { /* storage blocked: celebrate again next time */ }
  }

  function render(container, light, options) {
    if (!LABELS.hasOwnProperty(light)) throw new Error("Unknown goal light: " + light);
    options = options || {};
    var previous = lastLight.get(container);
    lastLight.set(container, light);

    container.className = "pw-goal-light pw-goal-light--" + light;
    container.setAttribute("role", "status");
    container.setAttribute("aria-live", "polite");
    container.innerHTML = '<span class="pw-goal-light__dot" aria-hidden="true"></span>' +
      '<span class="pw-goal-light__label"></span>';
    container.querySelector(".pw-goal-light__label").textContent = LABELS[light];

    if (light === "celebrate" && previous !== "celebrate" && !alreadyCelebrated(options.goalKey)) {
      markCelebrated(options.goalKey);
      celebrate();
    }
  }

  /* ---------- celebration: fireworks, confetti and emoji ---------- */

  var COLORS = ["#2BB673", "#5FD3B4", "#F2B33D", "#F07A62", "#7C6CF2", "#3AA0FF", "#FFFFFF"];
  var EMOJI = ["🎉", "🎊", "✨", "🥳", "🎆", "💚"];

  function celebrate() {
    showBanner();
    if (reducedMotion()) return;

    var canvas = document.createElement("canvas");
    canvas.className = "pw-celebration";
    canvas.setAttribute("aria-hidden", "true");
    document.body.appendChild(canvas);
    var ctx = canvas.getContext("2d");
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var W, H;
    function resize() {
      W = window.innerWidth; H = window.innerHeight;
      canvas.width = W * dpr; canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener("resize", resize);

    var rockets = [], sparks = [], confetti = [], emoji = [];
    var start = performance.now(), lastLaunch = 0;

    function rand(a, b) { return a + Math.random() * (b - a); }
    function pick(list) { return list[Math.floor(Math.random() * list.length)]; }

    for (var i = 0; i < 140; i++) {
      confetti.push({
        x: rand(0, W), y: rand(-H, 0), w: rand(6, 11), h: rand(8, 16),
        vy: rand(2, 4.5), vx: rand(-1, 1), rot: rand(0, Math.PI), vr: rand(-0.15, 0.15), color: pick(COLORS)
      });
    }
    for (var j = 0; j < 18; j++) {
      emoji.push({ x: rand(0.05, 0.95) * W, y: H + rand(0, 300), vy: rand(2, 3.6), size: rand(26, 44), ch: pick(EMOJI), sway: rand(0, 6) });
    }

    function launch() {
      rockets.push({ x: rand(0.15, 0.85) * W, y: H, vy: -rand(9, 12.5), target: rand(0.15, 0.45) * H, color: pick(COLORS) });
    }

    function explode(r) {
      var n = 70;
      for (var k = 0; k < n; k++) {
        var a = (Math.PI * 2 * k) / n, s = rand(2, 6.5);
        sparks.push({ x: r.x, y: r.y, vx: Math.cos(a) * s, vy: Math.sin(a) * s, life: 1, color: Math.random() < 0.3 ? "#FFFFFF" : r.color });
      }
    }

    function frame(now) {
      var t = now - start;
      ctx.clearRect(0, 0, W, H);

      if (t < CELEBRATION_MS - 1500 && now - lastLaunch > 380) { launch(); lastLaunch = now; }

      rockets = rockets.filter(function (r) {
        r.y += r.vy; r.vy += 0.12;
        ctx.fillStyle = r.color; ctx.beginPath(); ctx.arc(r.x, r.y, 3, 0, Math.PI * 2); ctx.fill();
        if (r.y <= r.target || r.vy >= 0) { explode(r); return false; }
        return true;
      });

      sparks = sparks.filter(function (p) {
        p.x += p.vx; p.y += p.vy; p.vy += 0.06; p.vx *= 0.985; p.life -= 0.016;
        ctx.globalAlpha = Math.max(p.life, 0); ctx.fillStyle = p.color;
        ctx.beginPath(); ctx.arc(p.x, p.y, 2.4, 0, Math.PI * 2); ctx.fill();
        return p.life > 0;
      });
      ctx.globalAlpha = 1;

      confetti.forEach(function (c) {
        c.y += c.vy; c.x += c.vx + Math.sin((t + c.x) / 300) * 0.6; c.rot += c.vr;
        ctx.save(); ctx.translate(c.x, c.y); ctx.rotate(c.rot);
        ctx.fillStyle = c.color; ctx.fillRect(-c.w / 2, -c.h / 2, c.w, c.h); ctx.restore();
      });

      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      emoji.forEach(function (e) {
        e.y -= e.vy;
        ctx.font = e.size + "px 'Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji',sans-serif";
        ctx.fillText(e.ch, e.x + Math.sin((t / 400) + e.sway) * 14, e.y);
      });

      var fade = t > CELEBRATION_MS - 800 ? Math.max(0, (CELEBRATION_MS - t) / 800) : 1;
      canvas.style.opacity = String(fade);

      if (t < CELEBRATION_MS) requestAnimationFrame(frame);
      else { window.removeEventListener("resize", resize); canvas.remove(); }
    }
    requestAnimationFrame(frame);
  }

  function showBanner() {
    var old = document.querySelector(".pw-celebration-banner");
    if (old) old.remove();
    var banner = document.createElement("div");
    banner.className = "pw-celebration-banner";
    banner.setAttribute("role", "alert");
    banner.innerHTML = '<span class="pw-celebration-banner__emoji" aria-hidden="true">🎉🎊</span>' +
      '<strong>הגעת ליעד!</strong><span>כל הכבוד, החיסכון שלך הצליח.</span>';
    document.body.appendChild(banner);
    setTimeout(function () { banner.classList.add("pw-celebration-banner--out"); }, CELEBRATION_MS - 600);
    setTimeout(function () { banner.remove(); }, CELEBRATION_MS);
  }

  window.PocketWiseGoalLight = { render: render, celebrate: celebrate };
})();
