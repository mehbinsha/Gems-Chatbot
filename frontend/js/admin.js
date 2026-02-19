const API_BASE = "/api/admin";

const loginCard = document.getElementById("login-card");
const dashboard = document.getElementById("dashboard");
const loginForm = document.getElementById("login-form");
const loginError = document.getElementById("login-error");
const logoutBtn = document.getElementById("logout-btn");

const intentForm = document.getElementById("intent-form");
const formTitle = document.getElementById("form-title");
const intentId = document.getElementById("intent-id");
const topicInput = document.getElementById("topic");
const detailsInput = document.getElementById("details");
const responsesInput = document.getElementById("responses");
const cancelEditBtn = document.getElementById("cancel-edit");
const formError = document.getElementById("form-error");
const intentList = document.getElementById("intent-list");
const loginBtn = document.getElementById("login-btn");
const saveBtn = document.getElementById("save-btn");
const searchInput = document.getElementById("intent-search");
const intentCountEl = document.getElementById("intent-count");
const patternCountEl = document.getElementById("pattern-count");
const responseCountEl = document.getElementById("response-count");
const previewOutput = document.getElementById("preview-output");
const toast = document.getElementById("toast");
const prefForm = document.getElementById("pref-form");
const prefRulesList = document.getElementById("pref-rules-list");
const prefAddBtn = document.getElementById("pref-add-btn");
const prefSaveBtn = document.getElementById("pref-save-btn");
const prefError = document.getElementById("pref-error");
const historyList = document.getElementById("history-list");
const refreshHistoryBtn = document.getElementById("refresh-history-btn");

let allIntents = [];
let toastTimer = null;

async function safeJson(response) {
  try {
    return await response.json();
  } catch (_) {
    return {};
  }
}

function getToken() {
  return localStorage.getItem("admin_token");
}

function setToken(token) {
  localStorage.setItem("admin_token", token);
}

function clearToken() {
  localStorage.removeItem("admin_token");
}

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("show");
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 1800);
}

function requireAuthHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getToken()}`,
  };
}

function toLines(value) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function showLogin() {
  loginCard.classList.remove("hidden");
  dashboard.classList.add("hidden");
}

function showDashboard() {
  loginCard.classList.add("hidden");
  dashboard.classList.remove("hidden");
}

function resetForm() {
  intentId.value = "";
  topicInput.value = "";
  detailsInput.value = "";
  responsesInput.value = "";
  formTitle.textContent = "Create Intent";
  cancelEditBtn.classList.add("hidden");
  formError.textContent = "";
  if (previewOutput) {
    previewOutput.classList.add("hidden");
    previewOutput.textContent = "";
  }
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function fetchIntents() {
  try {
    const response = await fetch(`${API_BASE}/intents`, {
      headers: requireAuthHeaders(),
    });

    if (response.status === 401) {
      clearToken();
      showLogin();
      return;
    }

    const data = await safeJson(response);
    if (!response.ok) {
      formError.textContent = data.error || "Failed to fetch intents.";
      return;
    }

    allIntents = data.intents || [];
    renderIntentList(allIntents);
    updateStats(allIntents);
  } catch (_) {
    formError.textContent = "Unable to reach server.";
  }
}

async function fetchResultPreferences() {
  if (!prefRulesList) return;
  const response = await fetch(`${API_BASE}/result-preferences`, {
    headers: requireAuthHeaders(),
  });
  const data = await safeJson(response);
  if (!response.ok) {
    prefError.textContent = data.error || "Failed to load preferences.";
    return;
  }
  renderPreferenceRows(data.rules || []);
  prefError.textContent = "";
}

function makePreferenceRow(rule = { course: "", min_marks: "" }) {
  const row = document.createElement("div");
  row.className = "pref-rule-row";

  const courseInput = document.createElement("input");
  courseInput.type = "text";
  courseInput.placeholder = "Course name";
  courseInput.className = "pref-course";
  courseInput.value = String(rule.course || "");
  courseInput.required = true;

  const minInput = document.createElement("input");
  minInput.type = "number";
  minInput.className = "pref-min-marks";
  minInput.placeholder = "Min marks";
  minInput.min = "0";
  minInput.max = "100";
  minInput.step = "0.01";
  minInput.value = rule.min_marks === "" ? "" : String(rule.min_marks ?? "");
  minInput.required = true;

  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.className = "danger pref-remove-btn";
  removeBtn.textContent = "Remove";
  removeBtn.addEventListener("click", () => {
    row.remove();
    if (!prefRulesList.querySelector(".pref-rule-row")) {
      prefRulesList.appendChild(makePreferenceRow());
    }
  });

  row.appendChild(courseInput);
  row.appendChild(minInput);
  row.appendChild(removeBtn);
  return row;
}

function renderPreferenceRows(rules) {
  if (!prefRulesList) return;
  prefRulesList.innerHTML = "";

  const list = Array.isArray(rules) && rules.length ? rules : [{ course: "", min_marks: "" }];
  list.forEach((rule) => {
    prefRulesList.appendChild(makePreferenceRow(rule));
  });
}

function readPreferenceRules() {
  if (!prefRulesList) return [];
  const rows = Array.from(prefRulesList.querySelectorAll(".pref-rule-row"));
  const rules = [];

  for (const row of rows) {
    const course = row.querySelector(".pref-course")?.value?.trim() || "";
    const minRaw = row.querySelector(".pref-min-marks")?.value?.trim() || "";

    if (!course && !minRaw) {
      continue;
    }

    const minMarks = Number(minRaw);
    if (!course) {
      throw new Error("Course name is required for each rule.");
    }
    if (Number.isNaN(minMarks) || minMarks < 0 || minMarks > 100) {
      throw new Error(`Min marks for "${course}" must be between 0 and 100.`);
    }

    rules.push({
      course,
      min_marks: minMarks,
    });
  }

  if (!rules.length) {
    throw new Error("Add at least one course rule.");
  }
  return rules;
}

async function fetchResultHistory() {
  if (!historyList) return;
  const response = await fetch(`${API_BASE}/result-history?limit=100`, {
    headers: requireAuthHeaders(),
  });
  const data = await safeJson(response);
  if (!response.ok) {
    historyList.innerHTML = "<p>Failed to load history.</p>";
    return;
  }
  const items = data.items || [];
  if (!items.length) {
    historyList.innerHTML = "<p>No uploaded result history yet.</p>";
    return;
  }
  historyList.innerHTML = items
    .map(
      (item) => `
      <div class="history-row">
        <h4>${escapeHtml(item.student_name || "Unknown")} - ${Number(item.average || 0).toFixed(2)}%</h4>
        <p class="history-meta">Total: ${item.total || 0} | File: ${escapeHtml(item.source_filename || "-")}</p>
        <p class="history-meta">Courses: ${escapeHtml((item.recommended_courses || []).join(", ") || "-")}</p>
        <p class="history-meta">At: ${escapeHtml(item.analyzed_at || "-")}</p>
      </div>
    `
    )
    .join("");
}

function updateStats(intents) {
  const intentCount = intents.length;
  const patternCount = intents.reduce((sum, x) => sum + (x.patterns || []).length, 0);
  const responseCount = intents.reduce((sum, x) => sum + (x.responses || []).length, 0);

  if (intentCountEl) intentCountEl.textContent = String(intentCount);
  if (patternCountEl) patternCountEl.textContent = String(patternCount);
  if (responseCountEl) responseCountEl.textContent = String(responseCount);
}

function renderIntentList(intents) {
  if (!intents.length) {
    intentList.innerHTML = "<p>No intents found.</p>";
    return;
  }

  intentList.innerHTML = intents
    .map(
      (intent) => `
      <div class="intent-row">
        <h3>${escapeHtml(intent.tag)}</h3>
        <p><strong>Patterns:</strong> ${(intent.patterns || []).length}</p>
        <p><strong>Responses:</strong> ${(intent.responses || []).length}</p>
        <div class="actions">
          <button onclick="handleEdit(${intent.id})">Edit</button>
          <button class="secondary" onclick="handlePreview(${intent.id})">Preview</button>
          <button class="danger" onclick="handleDelete(${intent.id})">Delete</button>
        </div>
      </div>
    `
    )
    .join("");

  window.currentIntents = intents;
}

async function handleEdit(id) {
  const intent = (window.currentIntents || []).find((x) => x.id === id);
  if (!intent) return;

  intentId.value = intent.id;
  topicInput.value = intent.tag.replaceAll("_", " ");
  detailsInput.value = "";
  responsesInput.value = (intent.responses || []).join("\n");
  formTitle.textContent = "Edit Intent";
  cancelEditBtn.classList.remove("hidden");
  formError.textContent = "Details are optional on edit. Add keywords if you want regenerated triggers.";
  showToast(`Editing: ${intent.tag}`);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function handleDelete(id) {
  if (!confirm("Delete this intent?")) return;

  const response = await fetch(`${API_BASE}/intents/${id}`, {
    method: "DELETE",
    headers: requireAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) {
    alert(data.error || "Delete failed.");
    return;
  }

  await fetchIntents();
  showToast("Intent deleted");
}

async function handlePreview(id) {
  const response = await fetch(`${API_BASE}/intents/${id}/preview`, {
    headers: requireAuthHeaders(),
  });
  const data = await response.json();
  if (!response.ok) {
    alert(data.error || "Preview failed.");
    return;
  }

  if (previewOutput) {
    previewOutput.classList.remove("hidden");
    previewOutput.textContent = `Preview Reply:\n${data.preview}`;
  }
  showToast("Preview loaded");
}

window.handleEdit = handleEdit;
window.handleDelete = handleDelete;
window.handlePreview = handlePreview;

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginError.textContent = "";
  loginBtn.disabled = true;
  loginBtn.textContent = "Signing in...";

  const formData = new FormData(loginForm);
  const payload = {
    email: String(formData.get("email") || "").trim(),
    password: String(formData.get("password") || ""),
  };

  try {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await safeJson(response);

    if (!response.ok) {
      loginError.textContent = data.error || "Login failed.";
      loginBtn.disabled = false;
      loginBtn.textContent = "Log In";
      return;
    }

    if (!data.token) {
      loginError.textContent = "Login failed: missing token in response.";
      loginBtn.disabled = false;
      loginBtn.textContent = "Log In";
      return;
    }

    setToken(data.token);
    showDashboard();
    await fetchIntents();
    await fetchResultPreferences();
    await fetchResultHistory();
    showToast("Login successful");
  } catch (_) {
    loginError.textContent = "Unable to reach server.";
  } finally {
    loginBtn.disabled = false;
    loginBtn.textContent = "Log In";
  }
});

logoutBtn.addEventListener("click", () => {
  clearToken();
  showLogin();
  showToast("Logged out");
});

intentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  formError.textContent = "";
  saveBtn.disabled = true;
  saveBtn.textContent = "Saving...";

  const payload = {
    topic: topicInput.value.trim(),
    details: detailsInput.value.trim() || topicInput.value.trim(),
    responses: toLines(responsesInput.value),
  };

  const id = intentId.value.trim();
  const isEdit = Boolean(id);
  const url = isEdit ? `${API_BASE}/intents/${id}/smart` : `${API_BASE}/intents/smart`;
  const method = isEdit ? "PUT" : "POST";

  try {
    const response = await fetch(url, {
      method,
      headers: requireAuthHeaders(),
      body: JSON.stringify(payload),
    });
    const data = await safeJson(response);

    if (!response.ok) {
      formError.textContent = data.error || "Save failed.";
      return;
    }

    const generated = data.generated || null;
    resetForm();
    if (previewOutput && generated) {
      previewOutput.classList.remove("hidden");
      previewOutput.textContent =
        `Generated Tag: ${generated.tag}\n` +
        `Generated Patterns: ${(generated.patterns || []).length}`;
    }
    await fetchIntents();
    showToast(isEdit ? "Intent updated" : "Intent created");
  } catch (_) {
    formError.textContent = "Unable to reach server.";
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = "Save";
  }
});

cancelEditBtn.addEventListener("click", () => {
  resetForm();
});

if (searchInput) {
  searchInput.addEventListener("input", () => {
    const q = searchInput.value.trim().toLowerCase();
    if (!q) {
      renderIntentList(allIntents);
      return;
    }
    const filtered = allIntents.filter((x) => (x.tag || "").toLowerCase().includes(q));
    renderIntentList(filtered);
  });
}

if (prefForm) {
  renderPreferenceRows([]);

  if (prefAddBtn) {
    prefAddBtn.addEventListener("click", () => {
      prefRulesList.appendChild(makePreferenceRow());
    });
  }

  prefForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    prefError.textContent = "";
    prefSaveBtn.disabled = true;
    prefSaveBtn.textContent = "Saving...";

    let rules;
    try {
      rules = readPreferenceRules();
    } catch (error) {
      prefError.textContent = error.message || "Invalid course preferences.";
      prefSaveBtn.disabled = false;
      prefSaveBtn.textContent = "Save Preferences";
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/result-preferences`, {
        method: "PUT",
        headers: requireAuthHeaders(),
        body: JSON.stringify({ rules }),
      });
      const data = await safeJson(response);
      if (!response.ok) {
        prefError.textContent = data.error || "Failed to save preferences.";
        return;
      }
      renderPreferenceRows(data.rules || []);
      showToast("Result preferences updated");
      prefError.textContent = "";
    } catch (_) {
      prefError.textContent = "Unable to reach server.";
    } finally {
      prefSaveBtn.disabled = false;
      prefSaveBtn.textContent = "Save Preferences";
    }
  });
}

if (refreshHistoryBtn) {
  refreshHistoryBtn.addEventListener("click", async () => {
    refreshHistoryBtn.disabled = true;
    await fetchResultHistory();
    refreshHistoryBtn.disabled = false;
    showToast("History refreshed");
  });
}

if (getToken()) {
  showDashboard();
  fetchIntents();
  fetchResultPreferences();
  fetchResultHistory();
} else {
  showLogin();
}
