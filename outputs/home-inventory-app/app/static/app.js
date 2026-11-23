const toast = (message) => {
  const el = document.querySelector("#toast");
  el.textContent = message;
  el.hidden = false;
  setTimeout(() => { el.hidden = true; }, 2400);
};

// Room dropdowns: choosing "Custom room…" swaps the select for a free-text
// input with the same name, so form serialization keeps working.
document.querySelectorAll("select[data-room-select]").forEach((select) => {
  select.addEventListener("change", () => {
    if (select.value !== "__custom__") return;
    const input = document.createElement("input");
    input.name = select.name;
    input.placeholder = "Type room name";
    if (select.required) input.required = true;
    select.replaceWith(input);
    input.focus();
  });
});

const asJson = (form) => {
  const data = new FormData(form);
  const out = {};
  for (const [key, value] of data.entries()) out[key] = value;
  for (const checkbox of form.querySelectorAll("input[type=checkbox]")) {
    out[checkbox.name] = checkbox.checked ? 1 : 0;
  }
  return out;
};

document.querySelectorAll(".segmented [data-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".segmented button").forEach((b) => b.classList.remove("active"));
    button.classList.add("active");
    const count = Number(button.dataset.mode);
    document.querySelectorAll("[data-create-card]").forEach((card, index) => {
      card.hidden = index >= count;
    });
  });
});

document.querySelectorAll("[data-create-card]").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button");
    button.disabled = true;
    button.textContent = "Creating...";
    const data = new FormData(form);
    if (!form.querySelector("input[name=inaccessible]").checked) data.set("inaccessible", "0");
    const res = await fetch("/api/boxes", { method: "POST", body: data });
    if (!res.ok) {
      toast("Could not create box");
      button.disabled = false;
      button.textContent = "Create and detect items";
      return;
    }
    const json = await res.json();
    toast("Container created");
    window.location.href = json.url;
  });
});

document.querySelectorAll(".ajax-json").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const res = await fetch(form.dataset.url, {
      method: form.dataset.method || "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(asJson(form)),
    });
    toast(res.ok ? "Saved" : "Save failed");
  });
});

const boxDetail = document.querySelector("[data-box-id]");
if (boxDetail) {
  const boxId = boxDetail.dataset.boxId;

  document.querySelector("[data-add-item]")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const res = await fetch(`/api/boxes/${boxId}/items`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(asJson(form)),
    });
    if (res.ok) location.reload(); else toast("Could not add item");
  });

  document.querySelector("[data-photo-upload]")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const res = await fetch(`/api/boxes/${boxId}/photos`, { method: "POST", body: new FormData(form) });
    if (res.ok) location.reload(); else toast("Upload failed");
  });

  document.querySelectorAll("[data-reprocess-photo]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      const original = button.textContent;
      button.textContent = "Running vision...";
      const photoId = button.dataset.photoId;
      const res = await fetch(`/api/boxes/${boxId}/photos/${photoId}/reprocess`, { method: "POST" });
      if (res.ok) {
        const json = await res.json();
        if (json.llm_used) {
          toast(`LLM used (${json.model}) in ${json.duration_ms}ms. ${json.suggestions.length} suggestion(s).`);
        } else {
          const reason = json.vision_error || `provider=${json.provider}`;
          toast(`LLM not used: ${reason}`);
        }
        setTimeout(() => location.reload(), 900);
      } else {
        toast("Vision rerun failed");
        button.disabled = false;
        button.textContent = original;
      }
    });
  });

  document.querySelectorAll("[data-save-item]").forEach((button) => {
    button.addEventListener("click", async () => {
      const row = button.closest("[data-item-id]");
      const data = {};
      row.querySelectorAll("input, select").forEach((field) => { if (field.name) data[field.name] = field.value; });
      const res = await fetch(`/api/box-items/${row.dataset.itemId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      toast(res.ok ? "Item saved" : "Item save failed");
    });
  });

  document.querySelectorAll("[data-delete-item]").forEach((button) => {
    button.addEventListener("click", async () => {
      const row = button.closest("[data-item-id]");
      const res = await fetch(`/api/box-items/${row.dataset.itemId}`, { method: "DELETE" });
      if (res.ok) row.remove(); else toast("Delete failed");
    });
  });

  document.querySelectorAll("[data-move-target]").forEach((select) => {
    select.addEventListener("change", async () => {
      if (!select.value) return;
      const row = select.closest("[data-item-id]");
      const res = await fetch(`/api/box-items/${row.dataset.itemId}/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_box_id: select.value }),
      });
      if (res.ok) row.remove(); else toast("Move failed");
    });
  });

  document.querySelectorAll("[data-confirm-suggestion]").forEach((button) => {
    button.addEventListener("click", async () => {
      const row = button.closest("[data-suggestion-id]");
      const res = await fetch(`/api/detections/${row.dataset.suggestionId}/confirm`, { method: "POST" });
      if (res.ok) location.reload(); else toast("Confirm failed");
    });
  });

  document.querySelectorAll("[data-dismiss-suggestion]").forEach((button) => {
    button.addEventListener("click", async () => {
      const row = button.closest("[data-suggestion-id]");
      const res = await fetch(`/api/detections/${row.dataset.suggestionId}`, { method: "DELETE" });
      if (res.ok) row.remove(); else toast("Dismiss failed");
    });
  });

  document.querySelector("[data-delete-container]")?.addEventListener("click", async () => {
    if (!confirm("Delete this container and all its contents? This cannot be undone.")) return;
    const res = await fetch(`/api/boxes/${boxId}`, { method: "DELETE" });
    if (res.ok) window.location.href = "/boxes"; else toast("Delete failed");
  });

  document.querySelectorAll("[data-estimate-cost]").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      const original = button.textContent;
      button.textContent = "Estimating...";
      const itemId = button.dataset.itemId;
      const res = await fetch(`/api/items/${itemId}/cost-estimate`, { method: "POST" });
      if (res.ok) {
        toast("Cost estimate added");
        setTimeout(() => location.reload(), 700);
      } else {
        const body = await res.json().catch(() => ({}));
        toast(body.detail || "Cost estimate failed");
        button.disabled = false;
        button.textContent = original;
      }
    });
  });

  document.querySelector("[data-estimate-all-costs]")?.addEventListener("click", async (event) => {
    const button = event.currentTarget;
    if (button.disabled) return;
    button.disabled = true;
    const original = button.textContent;
    button.textContent = "Estimating all...";
    const res = await fetch(`/api/boxes/${boxId}/cost-estimates`, { method: "POST" });
    if (res.ok) {
      const json = await res.json();
      toast(`Estimated ${json.estimated.length}, skipped ${json.skipped.length}, failed ${json.failed.length}`);
      setTimeout(() => location.reload(), 900);
    } else {
      toast("Batch cost estimate failed");
      button.disabled = false;
      button.textContent = original;
    }
  });
}
