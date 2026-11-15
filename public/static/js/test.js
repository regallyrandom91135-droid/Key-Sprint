(() => {
  const input = document.getElementById("typed_text");
  if (!input) return;
  const timer = document.getElementById("timer");
  const durationInput = document.getElementById("duration");
  const count = document.getElementById("live-count");
  const form = document.getElementById("test-form");
  const finish = document.getElementById("finish-button");
  let remaining = 60;
  let startedAt = null;
  let interval = null;
  let finished = false;

  function finishTest() {
    if (finished) return;
    finished = true;
    clearInterval(interval);
    input.readOnly = true;
    durationInput.value = String(Math.max(1, 60 - remaining));
    timer.textContent = "0";
    finish.textContent = "Saving result…";
    form.requestSubmit();
  }

  input.addEventListener("input", () => {
    const words = input.value.trim() ? input.value.trim().split(/\s+/).length : 0;
    count.textContent = `${words} word${words === 1 ? "" : "s"} typed`;
    if (startedAt === null) {
      startedAt = Date.now();
      interval = setInterval(() => {
        remaining -= 1;
        timer.textContent = String(remaining);
        if (remaining <= 0) finishTest();
      }, 1000);
    }
  });

  form.addEventListener("submit", (event) => {
    if (!input.value.trim()) {
      event.preventDefault();
      input.focus();
      return;
    }
    if (!finished) {
      finished = true;
      clearInterval(interval);
      durationInput.value = String(Math.max(1, Math.round((Date.now() - startedAt) / 1000)));
    }
  });
})();
