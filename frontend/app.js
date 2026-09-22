const API_URL = "http://localhost:8010";

// ---- DOM refs ----
const chatScroll = document.getElementById("chat-scroll");
const chatWindow = document.getElementById("chat-window");
const emptyState = document.getElementById("empty-state");
const emptyGreeting = document.getElementById("empty-greeting");
const inputForm = document.getElementById("input-form");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");
const statusEl = document.getElementById("status");
const voicePreview = document.getElementById("voice-preview");
const voicePreviewText = document.getElementById("voice-preview-text");

const headerConnectBtn = document.getElementById("header-connect-btn");
const headerConnectLabel = document.getElementById("header-connect-label");
const headerDisconnectBtn = document.getElementById("header-disconnect-btn");
const sidebarConnectStatus = document.getElementById("sidebar-connect-status");
const sidebarDisconnectBtn = document.getElementById("sidebar-disconnect-btn");
const panelConnectBadge = document.getElementById("panel-connect-badge");
const panelConnectedView = document.getElementById("panel-connected-view");
const panelDisconnectedView = document.getElementById("panel-disconnected-view");
const panelConnectBtn = document.getElementById("panel-connect-btn");
const panelDisconnectBtn = document.getElementById("panel-disconnect-btn");
const viewCalendarBtn = document.getElementById("view-calendar-btn");

const recentActionCard = document.getElementById("recent-action-card");
const recentActionBody = document.getElementById("recent-action-body");

const sidebar = document.getElementById("sidebar");
const contextPanel = document.getElementById("context-panel");
const scrim = document.getElementById("scrim");
const menuBtn = document.getElementById("menu-btn");
const mobileContextBtn = document.getElementById("mobile-context-btn");
const sidebarCloseBtn = document.getElementById("sidebar-close");
const contextCloseBtn = document.getElementById("context-close");
const newChatBtn = document.getElementById("new-chat-btn");
const conversationList = document.getElementById("conversation-list");

// ============================================================
// Greeting (time-aware, purely cosmetic)
// ============================================================
(function setGreeting() {
  const hour = new Date().getHours();
  let greeting = "Good evening";
  if (hour < 12) greeting = "Good morning";
  else if (hour < 18) greeting = "Good afternoon";
  emptyGreeting.textContent = `${greeting} \u{1F44B}`;
})();

// ============================================================
// Mobile drawer handling
// ============================================================
function openDrawer(panel) {
  panel.classList.add("is-open");
  scrim.hidden = false;
  const isSidebar = panel === sidebar;
  (isSidebar ? menuBtn : mobileContextBtn).setAttribute("aria-expanded", "true");
}

function closeDrawers() {
  sidebar.classList.remove("is-open");
  contextPanel.classList.remove("is-open");
  scrim.hidden = true;
  menuBtn.setAttribute("aria-expanded", "false");
  mobileContextBtn.setAttribute("aria-expanded", "false");
}

menuBtn.addEventListener("click", () => openDrawer(sidebar));
mobileContextBtn.addEventListener("click", () => openDrawer(contextPanel));
sidebarCloseBtn.addEventListener("click", closeDrawers);
contextCloseBtn.addEventListener("click", closeDrawers);
scrim.addEventListener("click", closeDrawers);

// ============================================================
// New chat / conversation switching (client-side only —
// there is no multi-conversation backend, so this simply
// clears the active transcript).
// ============================================================
function startNewConversation() {
  chatWindow.innerHTML = "";
  chatWindow.hidden = true;
  emptyState.hidden = false;
  messageInput.value = "";
  statusEl.textContent = "";
  closeDrawers();
}

newChatBtn.addEventListener("click", startNewConversation);

conversationList.addEventListener("click", (e) => {
  const item = e.target.closest(".conversation-item");
  if (!item) return;
  conversationList.querySelectorAll(".conversation-item").forEach((el) => el.classList.remove("is-active"));
  item.classList.add("is-active");
  closeDrawers();
});

// ============================================================
// Message rendering
// ============================================================
function showConversationView() {
  if (emptyState.hidden) return;
  emptyState.hidden = true;
  chatWindow.hidden = false;
}

function scrollToBottom() {
  chatScroll.scrollTop = chatScroll.scrollHeight;
}

function addMessage(text, type) {
  showConversationView();

  const row = document.createElement("div");
  row.className = `msg-row ${type}`;

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = type === "user" ? "You" : "S";
  avatar.setAttribute("aria-hidden", "true");

  const body = document.createElement("div");
  body.className = "msg-body";

  const bubble = document.createElement("div");
  bubble.className = type === "error" ? "msg-bubble error" : "msg-bubble";
  bubble.textContent = text;

  body.appendChild(bubble);
  row.appendChild(avatar);
  row.appendChild(body);
  chatWindow.appendChild(row);
  scrollToBottom();
  return body;
}

function addTypingIndicator() {
  showConversationView();

  const row = document.createElement("div");
  row.className = "msg-row assistant";

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = "S";
  avatar.setAttribute("aria-hidden", "true");

  const body = document.createElement("div");
  body.className = "msg-body";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.innerHTML = `
    <span class="typing-indicator"><span></span><span></span><span></span></span>
  `;

  body.appendChild(bubble);
  row.appendChild(avatar);
  row.appendChild(body);
  chatWindow.appendChild(row);
  scrollToBottom();
  return row;
}

function checkIcon() {
  return '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>';
}

function formatEventDateTime(iso) {
  if (!iso) return { date: "", time: "" };
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return { date: iso, time: "" };
  const date = d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  const time = d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  return { date, time };
}

function addActionCard(action) {
  const row = document.createElement("div");
  row.className = "msg-row assistant";

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = "S";

  const body = document.createElement("div");
  body.className = "msg-body";

  const { date, time } = formatEventDateTime(action.start);

  const card = document.createElement("div");
  card.className = "action-card";
  card.innerHTML = `
    <div class="action-card-header">${checkIcon()}<span>Calendar event created</span></div>
    <div class="action-card-body">
      <span class="action-card-title"></span>
      <div class="action-card-meta">
        ${date ? `<span>${calendarIcon()} ${escapeHtml(date)}</span>` : ""}
        ${time ? `<span>${clockIcon()} ${escapeHtml(time)}</span>` : ""}
      </div>
    </div>
    <div class="action-card-footer">
      <span class="action-card-source">${calendarIcon()} Google Calendar</span>
      ${action.link ? `<a href="${escapeAttr(action.link)}" target="_blank" rel="noopener noreferrer">Open event &rarr;</a>` : ""}
    </div>
  `;
  card.querySelector(".action-card-title").textContent = action.title || "Untitled event";

  body.appendChild(card);
  row.appendChild(avatar);
  row.appendChild(body);
  chatWindow.appendChild(row);
  scrollToBottom();

  updateRecentAction(action, date, time);
}

function calendarIcon() {
  return '<svg viewBox="0 0 24 24" width="12" height="12" aria-hidden="true"><path d="M8 2v3M16 2v3M3.5 9h17M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>';
}

function clockIcon() {
  return '<svg viewBox="0 0 24 24" width="12" height="12" aria-hidden="true"><circle cx="12" cy="12" r="8.5" stroke="currentColor" stroke-width="1.6" fill="none"/><path d="M12 7.5V12l3 2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>';
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function escapeAttr(str) {
  return escapeHtml(str).replace(/"/g, "&quot;");
}

function addErrorCard(message) {
  showConversationView();

  const row = document.createElement("div");
  row.className = "msg-row assistant";

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = "S";

  const body = document.createElement("div");
  body.className = "msg-body";

  const card = document.createElement("div");
  card.className = "error-card";
  card.innerHTML = `
    <span class="error-card-title">Something went wrong</span>
    <span class="error-card-text"></span>
    <button type="button" class="ghost-btn retry-btn">Try again</button>
  `;
  card.querySelector(".error-card-text").textContent = message;

  body.appendChild(card);
  row.appendChild(avatar);
  row.appendChild(body);
  chatWindow.appendChild(row);
  scrollToBottom();

  return card.querySelector(".retry-btn");
}

function updateRecentAction(action, date, time) {
  recentActionCard.hidden = false;
  recentActionBody.innerHTML = `
    <div>
      <strong></strong>
      ${date || time ? `<span>${escapeHtml([date, time].filter(Boolean).join(", "))}</span>` : ""}
    </div>
  `;
  recentActionBody.querySelector("strong").textContent = action.title || "Untitled event";
}

// ============================================================
// Google Calendar connection status
// ============================================================
function setConnectionUi(connected, unknown) {
  if (unknown) {
    headerConnectLabel.textContent = "Status unknown";
    headerConnectBtn.classList.remove("is-connected");
    headerDisconnectBtn.hidden = true;
    sidebarConnectStatus.textContent = "Backend unreachable";
    sidebarConnectStatus.classList.remove("is-connected");
    sidebarConnectStatus.classList.add("is-error");
    sidebarDisconnectBtn.hidden = true;
    panelConnectBadge.textContent = "Unavailable";
    panelConnectBadge.classList.remove("is-connected");
    panelConnectedView.hidden = true;
    panelDisconnectedView.hidden = false;
    return;
  }

  if (connected) {
    headerConnectLabel.textContent = "Calendar connected";
    headerConnectBtn.classList.add("is-connected");
    headerDisconnectBtn.hidden = false;
    sidebarConnectStatus.textContent = "Connected ✓";
    sidebarConnectStatus.classList.add("is-connected");
    sidebarConnectStatus.classList.remove("is-error");
    sidebarDisconnectBtn.hidden = false;
    panelConnectBadge.textContent = "Connected";
    panelConnectBadge.classList.add("is-connected");
    panelConnectedView.hidden = false;
    panelDisconnectedView.hidden = true;
  } else {
    headerConnectLabel.textContent = "Connect calendar";
    headerConnectBtn.classList.remove("is-connected");
    headerDisconnectBtn.hidden = true;
    sidebarConnectStatus.textContent = "Not connected";
    sidebarConnectStatus.classList.remove("is-connected");
    sidebarConnectStatus.classList.remove("is-error");
    sidebarDisconnectBtn.hidden = true;
    panelConnectBadge.textContent = "Not connected";
    panelConnectBadge.classList.remove("is-connected");
    panelConnectedView.hidden = true;
    panelDisconnectedView.hidden = false;
  }
}

async function refreshConnectionStatus() {
  try {
    const res = await fetch(`${API_URL}/auth/status`, { credentials: "include" });
    const data = await res.json();
    setConnectionUi(!!data.connected, false);
    return data.connected;
  } catch (err) {
    setConnectionUi(false, true);
    return false;
  }
}

function goToGoogleLogin() {
  window.location.href = `${API_URL}/auth/login`;
}

async function disconnectGoogleCalendar() {
  sidebarDisconnectBtn.disabled = true;
  headerDisconnectBtn.disabled = true;
  if (panelDisconnectBtn) panelDisconnectBtn.disabled = true;
  statusEl.textContent = "Disconnecting Google Calendar…";

  try {
    await fetch(`${API_URL}/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } catch (err) {
    // Even if the request fails, refresh status below to reflect real state.
  } finally {
    await refreshConnectionStatus();
    sidebarDisconnectBtn.disabled = false;
    headerDisconnectBtn.disabled = false;
    if (panelDisconnectBtn) panelDisconnectBtn.disabled = false;
    statusEl.textContent = "";
  }
}

headerConnectBtn.addEventListener("click", () => {
  if (headerConnectBtn.classList.contains("is-connected")) return;
  goToGoogleLogin();
});
headerDisconnectBtn.addEventListener("click", disconnectGoogleCalendar);
sidebarDisconnectBtn.addEventListener("click", disconnectGoogleCalendar);
panelConnectBtn.addEventListener("click", goToGoogleLogin);
if (panelDisconnectBtn) panelDisconnectBtn.addEventListener("click", disconnectGoogleCalendar);
viewCalendarBtn.addEventListener("click", () => {
  window.open("https://calendar.google.com", "_blank", "noopener,noreferrer");
});

// If we just came back from the OAuth redirect, drop the query param and refresh status.
if (window.location.search.includes("connected=1")) {
  window.history.replaceState({}, "", window.location.pathname);
}
refreshConnectionStatus();

// ============================================================
// Sending messages
// ============================================================
async function sendMessage(text) {
  addMessage(text, "user");
  messageInput.value = "";
  voicePreview.hidden = true;
  sendBtn.disabled = true;

  const typingRow = addTypingIndicator();

  try {
    const res = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        message: text,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      if (res.status === 401) {
        await refreshConnectionStatus();
      }
      throw new Error(err.detail || `Request failed (${res.status})`);
    }

    const data = await res.json();
    typingRow.remove();

    if (data.reply) {
      addMessage(data.reply, "assistant");
    }

    if (data.action) {
      addActionCard(data.action);
    }
  } catch (err) {
    typingRow.remove();
    const retryBtn = addErrorCard(friendlyErrorMessage(err.message));
    retryBtn.addEventListener("click", () => sendMessage(text), { once: true });
  } finally {
    sendBtn.disabled = false;
  }
}

function friendlyErrorMessage(raw) {
  if (!raw) return "We couldn't process your request.";
  if (/not connected/i.test(raw)) return "Google Calendar isn't connected yet. Connect it to continue.";
  if (/network|failed to fetch/i.test(raw)) return "We couldn't reach Synq. Check your connection and try again.";
  return "We couldn't process your request.";
}

inputForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;
  sendMessage(text);
});

// ============================================================
// Suggestion cards & quick actions
// ============================================================
document.querySelectorAll(".suggestion-card, .quick-action-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const prompt = btn.getAttribute("data-prompt");
    if (!prompt) return;
    closeDrawers();
    sendMessage(prompt);
  });
});

// ============================================================
// Voice input (Web Speech API)
// ============================================================
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isRecording = false;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    isRecording = true;
    micBtn.classList.add("recording");
    micBtn.setAttribute("aria-label", "Stop voice input");
    statusEl.textContent = "Listening...";
    voicePreviewText.textContent = "";
    voicePreview.hidden = false;
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    messageInput.value = transcript;
    voicePreviewText.textContent = transcript;
    statusEl.textContent = "Review your request, then press send.";
  };

  recognition.onerror = (event) => {
    voicePreview.hidden = true;
    if (event.error === "not-allowed" || event.error === "service-not-allowed") {
      statusEl.textContent = "Microphone access denied. Enable it in your browser settings.";
    } else if (event.error === "no-speech") {
      statusEl.textContent = "We didn't catch that. Try again.";
    } else {
      statusEl.textContent = "Voice input isn't available right now.";
    }
  };

  recognition.onend = () => {
    isRecording = false;
    micBtn.classList.remove("recording");
    micBtn.setAttribute("aria-label", "Start voice input");
    if (statusEl.textContent === "Listening...") {
      statusEl.textContent = "";
    }
    if (!messageInput.value) {
      voicePreview.hidden = true;
    }
  };

  micBtn.addEventListener("click", () => {
    if (isRecording) {
      recognition.stop();
    } else {
      voicePreview.hidden = true;
      recognition.start();
    }
  });
} else {
  micBtn.disabled = true;
  micBtn.title = "Voice input is not supported in this browser";
}
