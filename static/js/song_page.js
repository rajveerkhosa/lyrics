(function () {
  const state = (window.SONG_PAGE_DATA && window.SONG_PAGE_DATA.selected) || {
    punjabi: true, romanization: true, translation: false
  };
  const label = { punjabi: "Punjabi", romanization: "Romanization", translation: "Translation" };

  function onCount() { return Object.values(state).filter(Boolean).length; }

  function setBtn(btn, isOn, disabled) {
    btn.textContent = label[btn.dataset.toggle];
    btn.className =
      "lyr-btn px-4 py-2 rounded-full transition-all duration-200 min-h-[44px] text-sm sm:text-base " +
      (isOn ? "bg-white text-black font-medium" : "bg-white/10 text-white hover:bg-white/20 ") +
      (disabled ? "opacity-50 cursor-not-allowed" : "hover:scale-105");
  }

  function renderLyrics(lyrics) {
    const data = Array.isArray(lyrics) ? lyrics : [];
    const root = document.getElementById("lyrics-container");
    if (!root) return;
    root.innerHTML = "";

    data.forEach((verse, vi) => {
      const wrap = document.createElement("div");
      wrap.className = "space-y-3";

      ["romanization", "punjabi", "translation"].forEach((key) => {
        if (!state[key]) return;
        const lines = verse[key] || [];
        const sec = document.createElement("div");
        sec.className = "space-y-1";
        lines.forEach((txt) => {
          const div = document.createElement("div");
          div.className =
            "text-sm sm:text-base lg:text-lg leading-relaxed " +
            (key === "punjabi" ? "text-white font-medium" :
             key === "romanization" ? "text-white/90" : "text-white/70 italic");
          div.textContent = txt;
          sec.appendChild(div);
        });
        wrap.appendChild(sec);
      });

      root.appendChild(wrap);
      if (vi < data.length - 1) root.appendChild(Object.assign(document.createElement("div"), { className: "h-2" }));
    });
  }

  function init() {
    const btns = Array.from(document.querySelectorAll(".lyr-btn"));
    btns.forEach((btn) => {
      const key = btn.dataset.toggle;
      setBtn(btn, state[key], onCount() === 1 && state[key]);
      btn.addEventListener("click", () => {
        if (onCount() === 1 && state[key]) return; // keep at least one on
        state[key] = !state[key];
        btns.forEach((b) => {
          const k = b.dataset.toggle;
          setBtn(b, state[k], onCount() === 1 && state[k]);
        });
        renderLyrics((window.SONG_PAGE_DATA && window.SONG_PAGE_DATA.lyrics) || []);
      });
    });

    renderLyrics((window.SONG_PAGE_DATA && window.SONG_PAGE_DATA.lyrics) || []);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
