/* editor.js — handles saving edits via fetch POST */

(function () {
  "use strict";

  function showToast(msg, isError = false) {
    let toast = document.getElementById("toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "toast";
      toast.className = "toast";
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.className = "toast" + (isError ? " error" : "");
    // Force reflow
    void toast.offsetHeight;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3000);
  }

  function getFormData() {
    const thinking = document.getElementById("edited_thinking")?.value ?? "";
    const answer = document.getElementById("edited_answer")?.value ?? "";
    const note = document.getElementById("edit_note")?.value ?? "";
    const include = document.getElementById("include_in_export")?.checked ?? true;
    return { edited_thinking: thinking, edited_answer: answer, edit_note: note, include_in_export: include };
  }

  async function saveEdit(url) {
    const btn = document.getElementById("save-btn");
    if (btn) btn.disabled = true;

    try {
      const data = getFormData();
      const resp = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`Server error ${resp.status}: ${text}`);
      }
      const json = await resp.json();
      showToast(`Saved at ${json.edited_at}`);

      // Update the "edited_at" display if present
      const editedAtEl = document.getElementById("edited-at-display");
      if (editedAtEl) editedAtEl.textContent = json.edited_at;
    } catch (err) {
      showToast(err.message, true);
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  // Auto-resize textareas
  function autoResize(el) {
    el.style.height = "auto";
    el.style.height = el.scrollHeight + "px";
  }

  document.addEventListener("DOMContentLoaded", () => {
    // Wire up save button
    const saveBtn = document.getElementById("save-btn");
    if (saveBtn) {
      const editUrl = saveBtn.dataset.editUrl;
      saveBtn.addEventListener("click", () => saveEdit(editUrl));
    }

    // Auto-resize textareas
    document.querySelectorAll("textarea").forEach((ta) => {
      autoResize(ta);
      ta.addEventListener("input", () => autoResize(ta));
    });

    // Keyboard shortcut: Cmd/Ctrl+S to save
    document.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        const saveBtn = document.getElementById("save-btn");
        if (saveBtn) saveBtn.click();
      }
    });
  });
})();
