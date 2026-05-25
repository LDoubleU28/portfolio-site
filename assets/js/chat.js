(function () {
  var launch = document.getElementById("chat-launch");
  var panel = document.getElementById("chat-panel");
  var close = document.getElementById("chat-close");
  var log = document.getElementById("chat-log");
  var form = document.getElementById("chat-form");
  var input = document.getElementById("chat-input");
  if (!launch || !panel) return;

  function isOpen() { return panel.classList.contains("open"); }
  function open() { panel.classList.add("open"); launch.classList.add("is-hidden"); input.focus(); }
  function hide() { panel.classList.remove("open"); launch.classList.remove("is-hidden"); }
  function toggle() { isOpen() ? hide() : open(); }

  launch.addEventListener("click", open);
  close.addEventListener("click", hide);

  var navTriggers = document.querySelectorAll("[data-chat-open]");
  for (var i = 0; i < navTriggers.length; i++) {
    navTriggers[i].addEventListener("click", function (e) { e.preventDefault(); toggle(); });
  }

  // Escape closes.
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && isOpen()) hide(); });

  // Click outside the panel closes (ignore the launch button and nav triggers).
  // Use capture phase so containment is checked before any handler can remove
  // the clicked node (e.g. a suggestion button) from the DOM.
  document.addEventListener("click", function (e) {
    if (!isOpen()) return;
    if (panel.contains(e.target)) return;
    if (launch.contains(e.target)) return;
    if (e.target.closest && e.target.closest("[data-chat-open]")) return;
    hide();
  }, true);

  // --- minimal, safe markdown -> HTML (escape first, then a few inline rules) ---
  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function inline(s) {
    s = esc(s);
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/\b_([^_]+)_\b/g, "<em>$1</em>");
    s = s.replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+|mailto:[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener">$1</a>'
    );
    return s;
  }
  function renderMarkdown(text) {
    var lines = String(text).replace(/\r/g, "").split("\n");
    var out = "";
    var para = [];
    var inList = false;
    function flushPara() {
      if (para.length) { out += "<p>" + para.join("<br>") + "</p>"; para = []; }
    }
    function closeList() { if (inList) { out += "</ul>"; inList = false; } }
    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i];
      var m = ln.match(/^\s*[-*]\s+(.*)$/);
      if (m) {
        flushPara();
        if (!inList) { out += "<ul>"; inList = true; }
        out += "<li>" + inline(m[1]) + "</li>";
      } else if (ln.trim() === "") {
        flushPara();
        closeList();
      } else {
        closeList();
        para.push(inline(ln));
      }
    }
    flushPara();
    closeList();
    return out;
  }

  function add(text, who) {
    var d = document.createElement("div");
    d.className = "chat-msg " + who;
    d.textContent = text;
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
    return d;
  }

  function ask(q) {
    add(q, "user");
    var sug = log.querySelector(".chat-suggest");
    if (sug) sug.remove();
    var pending = add("…", "bot pending");
    fetch("/api/ask", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question: q }),
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        pending.classList.remove("pending");
        if (d.answer) {
          pending.innerHTML = renderMarkdown(d.answer);
        } else {
          pending.textContent = "Sorry, something went wrong. Try again, or reach out via the links on the site.";
        }
        log.scrollTop = log.scrollHeight;
      })
      .catch(function () {
        pending.classList.remove("pending");
        pending.textContent = "Sorry, I could not reach the assistant right now.";
      });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var q = input.value.trim();
    if (!q) return;
    input.value = "";
    ask(q);
  });

  log.addEventListener("click", function (e) {
    if (e.target && e.target.matches(".chat-suggest button")) {
      ask(e.target.textContent);
    }
  });
})();
