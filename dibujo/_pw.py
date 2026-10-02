import sys, io, contextlib, importlib.util, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import matplotlib.pyplot as plt
S = []
orig = plt.Figure.savefig
def espia(self, *a, **k):
    r = self.canvas.get_renderer(); W = self.get_size_inches()[0]
    f = []
    for ax in list(self.axes):
        for art in ax.get_children():
            try: q = art.get_window_extent(renderer=r)
            except Exception: continue
            if q.x1/self.dpi > W + 0.02 or q.x0/self.dpi < -0.02:
                s = art.get_text()[:38] if hasattr(art,"get_text") else type(art).__name__
                if s: f.append((max(q.x1/self.dpi-W, -q.x0/self.dpi), q.x0/self.dpi, q.x1/self.dpi, s))
    for t in self.texts:
        q = t.get_window_extent(renderer=r)
        if q.x1/self.dpi > W + 0.02 or q.x0/self.dpi < -0.02:
            f.append((max(q.x1/self.dpi-W, -q.x0/self.dpi), q.x0/self.dpi, q.x1/self.dpi, "FIG:" + t.get_text()[:34]))
    S.append((os.path.basename(str(a[0])) if a else "?", W, sorted(f, reverse=True)[:4]))
    return orig(self, *a, **k)
plt.Figure.savefig = espia
for g in sys.argv[1:]:
    sp = importlib.util.spec_from_file_location("_m_" + g[:9], g)
    mo = importlib.util.module_from_spec(sp)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            sp.loader.exec_module(mo)
            (mo.main if hasattr(mo, "main") else mo.dibujar)()
    except Exception as e:
        print("  [!] %s: %s" % (g, str(e)[:70]))
for nom, W, f in S:
    if not f: continue
    print("  %-34s lienzo %.2f" % (nom[:34], W))
    for d, x0, x1, s in f:
        print("     +%.2f  [%.2f..%.2f]  %r" % (d, x0, x1, s))
