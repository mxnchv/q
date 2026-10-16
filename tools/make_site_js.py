"""Build the site's vacio.js from the editor page (mundos.html): same engine, no editing UI."""
import sys
src = open(sys.argv[1]).read()
a = src.index('<script>\n') + len('<script>\n'); b = src.rindex('\n</script>')
js = src[a:b]

def R(old, new, count=1):
    global js
    assert js.count(old) == count, old
    js = js.replace(old, new)

R("""  const stage = document.getElementById('stage');""", """  const stage = document.getElementById('vacio');
  if (!stage) return;""")
R("""  try { const saved = JSON.parse(localStorage.getItem('vacio-sound') || 'null'); if (saved) for (const v in S) Object.assign(S[v], saved[v] || {}); } catch (e) {}
  const save = () => { try { localStorage.setItem('vacio-sound', JSON.stringify(S)); } catch (e) {} };""",
"""  // the sound as tuned in the editor ("copiar ajustes"): anything listed here overrides the defaults
  const TUNED = {};
  for (const v in TUNED) Object.assign(S[v], TUNED[v]);""")
R("""  let fbAmount = calm ? 0 : 0.8, showNames = true,""", """  let fbAmount = calm ? 0 : 0.8, showNames = false,""")
# fade in / out around the master, and a sleep when silent
R("""      master = gainNode(0); master.connect(comp);""", """      master = gainNode(0); fadeG = gainNode(0); master.connect(fadeG); fadeG.connect(comp);""")
R("""    let nowT = 0, ac = null,""", """    let fadeG = null, sleepT = 0;
    let nowT = 0, ac = null,""")
R("""      get on() { return enabled; },
      async start() { if (!ac) init(); enabled = true; await ac.resume().catch(() => {}); },
      stop() { enabled = false; if (ac) set(master.gain, 0, 0.2); },""", """      get on() { return enabled; },
      // fade the whole world in (it starts making sound) or out (then it goes to sleep)
      fadeIn(sec = 2.5) {
        if (!ac) init();
        enabled = true; clearTimeout(sleepT); ac.resume().catch(() => {});
        const now = ac.currentTime, v = fadeG.gain.value;
        fadeG.gain.cancelScheduledValues(now); fadeG.gain.setValueAtTime(v, now); fadeG.gain.linearRampToValueAtTime(1, now + sec * (1 - v) + 0.01);
      },
      fadeOut(sec = 1.5) {
        if (!ac || !enabled) return;
        const now = ac.currentTime, v = fadeG.gain.value;
        fadeG.gain.cancelScheduledValues(now); fadeG.gain.setValueAtTime(v, now); fadeG.gain.linearRampToValueAtTime(0, now + sec * v + 0.01);
        clearTimeout(sleepT); sleepT = setTimeout(() => { enabled = false; ac.suspend(); }, sec * 1000 + 150);
      },""")
# drop the editor's mixer
a = js.index('  // ── the mixer panel'); b = js.index('  // ── input')
js = js[:a] + js[b:]
# new tail: input, sizing, and the visibility-driven loop
a = js.index('  // ── input')
js = js[:a] + """  // ── input: where the pointer is in the frame is where the camera turns (mouse: just hover;
  //    touch: hold and drag). Arrow keys steer while the game has focus.
  const fromEvent = e => { const r = stage.getBoundingClientRect(); steer.x = Math.max(-1, Math.min(1, (e.clientX - r.left) / r.width * 2 - 1)); steer.y = Math.max(-1, Math.min(1, (e.clientY - r.top) / r.height * 2 - 1)); };
  let touching = false;
  stage.addEventListener('pointermove', e => { if (e.pointerType === 'mouse' || touching) fromEvent(e); });
  stage.addEventListener('pointerdown', e => { touching = e.pointerType !== 'mouse'; if (touching) stage.setPointerCapture(e.pointerId); fromEvent(e); });
  const release = e => { if (e.pointerType !== 'mouse') { touching = false; steer.x = steer.y = 0; } };
  stage.addEventListener('pointerup', release); stage.addEventListener('pointercancel', release);
  stage.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') steer.x = steer.y = 0; });
  stage.addEventListener('contextmenu', e => e.preventDefault());
  const KEYS = { ArrowLeft: ['x', -0.7], ArrowRight: ['x', 0.7], ArrowUp: ['y', -0.7], ArrowDown: ['y', 0.7] };
  stage.addEventListener('keydown', e => { const k = KEYS[e.key]; if (k) { steer.keys[k[0]] = k[1]; e.preventDefault(); } });
  stage.addEventListener('keyup', e => { const k = KEYS[e.key]; if (k) steer.keys[k[0]] = 0; });
  stage.addEventListener('blur', () => { steer.keys.x = steer.keys.y = 0; });

  function resize() {
    const r = stage.getBoundingClientRect();
    if (!r.width || !r.height) return;
    dpr = Math.min(1.5, devicePixelRatio || 1);
    W = r.width; H = r.height;
    cv.width = fb.width = Math.round(W * dpr); cv.height = fb.height = Math.round(H * dpr);
    F = Math.max(W, H) * 0.62;
  }
  new ResizeObserver(resize).observe(stage); resize();

  // ── it only runs while you can see it: scroll it into view (or open Lab) and the sound fades in;
  //    scroll away or leave and the sound fades out and the picture stops
  let visible = false, running = false, last = 0, t = 0;
  function frame(now) {
    if (!visible) { running = false; return; }
    const dt = Math.min(0.05, (now - last) / 1000); last = now;
    t += dt;
    turn(dt);
    render(t, dt);
    sound.update(t, dt, env);
    requestAnimationFrame(frame);
  }
  // browsers only allow sound after a click or key on the page (the entry screen gives one)
  const mayPlay = () => !navigator.userActivation || navigator.userActivation.hasBeenActive;
  function show() {
    if (!running) { running = true; last = performance.now(); requestAnimationFrame(frame); }
    if (mayPlay()) sound.fadeIn();
  }
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; visible ? show() : sound.fadeOut(); }, { threshold: 0.25 }).observe(stage);
  // no click yet (a reload that skipped the entry screen): the first touch or key anywhere wakes the sound
  ['pointerdown', 'keydown'].forEach(ev => addEventListener(ev, () => { if (visible && !sound.on) sound.fadeIn(); }, true));
  addEventListener('lab:reset', () => sound.fadeOut(0.5));
})();
"""
header = """// Lab: an endless drift through the dark. Point (or drag) where you want to go.
// Forms grow out of origins on roots you can follow; each has its own synthesised voice (A minor),
// placed where the form is. Built from the editor page (vacio-editor.html in mxnchv/q): edit the
// sound there, "copiar ajustes", and paste the result into TUNED below.
"""
open(sys.argv[2], 'w').write(header + js.strip() + '\n')
print(len(js))
