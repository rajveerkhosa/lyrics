(function () {
  const state = (window.SONG_PAGE_DATA && window.SONG_PAGE_DATA.selected) || {
    punjabi: true,
    romanization: true,
    translation: false
  };

  function renderLyrics(lyrics) {
    const data = Array.isArray(lyrics) ? lyrics : [];
    const root = document.getElementById("lyrics-container");
    if (!root) return;

    if (data.length === 0) {
      root.innerHTML = '<p class="text-white/60 text-center py-8">No lyrics available yet.</p>';
      return;
    }

    root.innerHTML = "";

    data.forEach((line) => {
      const lineDiv = document.createElement("div");
      lineDiv.className = "space-y-2 pb-4 border-b border-white/10 last:border-0";
      lineDiv.id = `L${line.no}`;

      // Line number
      const lineNum = document.createElement("div");
      lineNum.className = "text-white/40 text-xs font-mono mb-2";
      lineNum.textContent = `Line ${line.no}`;
      lineDiv.appendChild(lineNum);

      // Punjabi (original)
      if (state.punjabi && line.original) {
        const punjabi = document.createElement("p");
        punjabi.className = "text-white font-medium text-base sm:text-lg leading-relaxed";
        punjabi.textContent = line.original;
        lineDiv.appendChild(punjabi);
      }

      // Romanization
      if (state.romanization && line.romanized) {
        const romanized = document.createElement("p");
        romanized.className = "text-white/80 italic text-sm sm:text-base leading-relaxed";
        romanized.textContent = line.romanized;
        lineDiv.appendChild(romanized);
      }

      // Translation
      if (state.translation && line.translation) {
        const translation = document.createElement("p");
        translation.className = "text-emerald-400 text-sm sm:text-base leading-relaxed";
        translation.textContent = line.translation;
        lineDiv.appendChild(translation);
      }

      root.appendChild(lineDiv);
    });
  }

  function updateButtons() {
    const btns = document.querySelectorAll(".btn-toggle");
    const onCount = Object.values(state).filter(Boolean).length;

    btns.forEach((btn) => {
      const key = btn.dataset.toggle;
      const isActive = state[key];
      const isLastActive = onCount === 1 && isActive;

      if (isActive) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }

      // Disable if it's the last active button
      btn.disabled = isLastActive;
      if (isLastActive) {
        btn.style.cursor = "not-allowed";
        btn.style.opacity = "0.7";
      } else {
        btn.style.cursor = "pointer";
        btn.style.opacity = "1";
      }
    });
  }

  function init() {
    const btns = document.querySelectorAll(".btn-toggle");

    btns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = btn.dataset.toggle;
        const onCount = Object.values(state).filter(Boolean).length;

        // Don't allow turning off the last active button
        if (onCount === 1 && state[key]) {
          return;
        }

        state[key] = !state[key];
        updateButtons();
        renderLyrics((window.SONG_PAGE_DATA && window.SONG_PAGE_DATA.lyrics) || []);
      });
    });

    updateButtons();
    renderLyrics((window.SONG_PAGE_DATA && window.SONG_PAGE_DATA.lyrics) || []);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();