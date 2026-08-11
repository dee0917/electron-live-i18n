/* electron-live-i18n loader — this tiny stub is what gets written into app.asar.
 * It fetches the real payload from the local server, so you can iterate on the
 * translation layer without ever touching the app bundle again.
 * NOTE: Electron's default CSP (script-src 'self' blob:) blocks eval(), so the
 * code is executed via a Blob URL instead.
 */
(function () {
  var URL_ = "__ELI_URL__", tries = 0;
  function inject() {
    tries++;
    fetch(URL_ + "?t=" + Date.now(), { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw 0; return r.text(); })
      .then(function (code) {
        var b = new Blob([code], { type: "text/javascript" });
        var s = document.createElement("script");
        s.onerror = function () { if (tries < 120) setTimeout(inject, 5000); };
        s.src = URL.createObjectURL(b);
        document.head.appendChild(s);
      })
      .catch(function () { if (tries < 120) setTimeout(inject, 5000); });
  }
  function boot() { setTimeout(inject, 1000); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
