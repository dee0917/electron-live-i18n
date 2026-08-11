/* electron-live-i18n runtime — injected into a packaged Electron app.
 * Walks the DOM, replaces known strings from the dictionary, and asks the local
 * server to translate anything new. Results are appended to the dictionary so the
 * app gets cleaner the more you use it.
 * Config is injected as window.__ELI_CONFIG = {api, skipSelectors:[...]}
 */
(function () {
  if (window.__eli_installed) return;
  window.__eli_installed = true;

  var CFG = window.__ELI_CONFIG || {};
  var API = CFG.api || "http://127.0.0.1:7799";
  var SKIP = CFG.skipSelectors || [];
  var DICT = CFG.dict || {};
  var pending = {};
  var CJK = /[\u4e00-\u9fff]/g;

  function mostlyForeign(t) {
    if (!t || t.length < 8 || t.length > 400) return false;
    if (!/[A-Za-z]{3,}/.test(t)) return false;
    var letters = (t.match(/[A-Za-z]/g) || []).length;
    var cjk = (t.match(CJK) || []).length;
    return letters >= 8 && cjk / Math.max(1, letters) < 0.12;
  }

  function skip(node) {
    var p = node.parentNode;
    if (!p) return true;
    var tag = (p.nodeName || "").toLowerCase();
    if (tag === "script" || tag === "style" || tag === "textarea") return true;
    if (p.isContentEditable) return true;
    for (var i = 0; i < SKIP.length; i++) {
      if (p.closest && p.closest(SKIP[i])) return true;
    }
    return false;
  }

  function fix(node) {
    var raw = node.nodeValue;
    if (!raw) return;
    var s = raw.trim();
    if (!s) return;
    if (DICT[s]) { node.nodeValue = raw.replace(s, DICT[s]); return; }
    if (!mostlyForeign(s)) return;
    if (pending[s]) {
      if (pending[s] !== true) node.nodeValue = raw.replace(s, pending[s]);
      return;
    }
    pending[s] = true;
    fetch(API + "/tr?q=" + encodeURIComponent(s), { cache: "force-cache" })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.t && d.t !== s) { pending[s] = d.t; DICT[s] = d.t; sweep(document.body); }
      })
      .catch(function () { pending[s] = s; });
  }

  function sweep(root) {
    if (!root) return;
    try {
      var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
      var n, batch = [];
      while ((n = w.nextNode())) { if (!skip(n)) batch.push(n); }
      batch.forEach(fix);
    } catch (e) { /* ignore */ }
  }

  var timer = null;
  function schedule() {
    if (timer) return;
    timer = setTimeout(function () { timer = null; sweep(document.body); }, 400);
  }

  function boot() {
    sweep(document.body);
    try {
      new MutationObserver(schedule).observe(document.body,
        { childList: true, subtree: true, characterData: true });
    } catch (e) { /* ignore */ }
    setInterval(function () { sweep(document.body); }, 5000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else setTimeout(boot, 500);

  window.__eli_sweep = sweep;
  window.__eli_dict = DICT;
})();
