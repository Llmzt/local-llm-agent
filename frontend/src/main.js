import "./styles.css";
import { marked } from "marked";
import DOMPurify from "dompurify";

const API_BASE_URL = "http://127.0.0.1:8000";
const SESSION_KEY = "agent1.session_id";
const DELETE_CONFIRM_MS = 4000;

const messagesEl = document.querySelector("#messages");
const formEl = document.querySelector("#chatForm");
const inputEl = document.querySelector("#messageInput");
const sendButtonEl = document.querySelector("#sendButton");
const newSessionButtonEl = document.querySelector("#newSessionButton");
const apiStatusEl = document.querySelector("#apiStatus");
const deleteSessionButtonEl = document.querySelector("#deleteSessionButton");
const sessionListEl = document.querySelector("#sessionList");
const toastViewportEl = document.querySelector("#toastViewport");

let sessionId = localStorage.getItem(SESSION_KEY);
let localMessages = [];
let sessionListSnapshot = "";
let pendingDeleteSessionId = null;
let pendingDeleteTimer = null;
let streamAssistantContentEl = null;
let pendingAssistantContent = "";
let pendingAssistantFrame = null;

renderSessionId();
renderMessages();
checkHealth();
loadSavedSession();
loadSessionList({ silent: true });

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();

  const text = inputEl.value.trim();
  if (!text) {
    return;
  }

  inputEl.value = "";
  appendMessage("user", text);
  appendMessage("thinking", "");
  setLoading(true);

  await nextFrame();

  try {
    await streamChatMessage(text);
  } catch {
    removeThinkingMessages();
    removeEmptyAssistantDraft();
    showError("无法连接 API，请确认后端服务已启动。");
  } finally {
    setLoading(false);
    inputEl.focus();
  }
});

inputEl.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey) {
    return;
  }

  event.preventDefault();

  if (!sendButtonEl.disabled) {
    formEl.requestSubmit();
  }
});

newSessionButtonEl.addEventListener("click", async () => {
  clearPendingDelete();
  sessionId = null;
  localMessages = [];
  localStorage.removeItem(SESSION_KEY);
  renderSessionId();
  renderMessages();
  renderSessionListFromCache();
  await loadSessionList({ silent: true });
  showToast("已创建新会话", "success");
  inputEl.focus();
});

deleteSessionButtonEl.addEventListener("click", async () => {
  if (!sessionId) {
    showToast("当前没有可删除的会话。", "info");
    return;
  }

  if (pendingDeleteSessionId !== sessionId) {
    pendingDeleteSessionId = sessionId;
    deleteSessionButtonEl.textContent = "再次点击删除";
    showToast("再次点击删除当前会话。", "info");

    window.clearTimeout(pendingDeleteTimer);
    pendingDeleteTimer = window.setTimeout(clearPendingDelete, DELETE_CONFIRM_MS);
    return;
  }

  await deleteCurrentSession();
});

async function checkHealth() {
  try {
    const response = await fetchWithRetry(`${API_BASE_URL}/health`);
    const body = await response.json();

    if (response.ok && body.ok) {
      apiStatusEl.textContent = "已连接";
      apiStatusEl.dataset.state = "ok";
      return;
    }

    apiStatusEl.textContent = "异常";
    apiStatusEl.dataset.state = "error";
    showError(body.error, "API 状态异常。");
  } catch {
    apiStatusEl.textContent = "未连接";
    apiStatusEl.dataset.state = "error";
    showError("无法连接 API，请确认后端服务已启动。");
  }
}

async function loadSavedSession() {
  if (!sessionId) {
    return;
  }

  try {
    const response = await fetchWithRetry(
      `${API_BASE_URL}/sessions/${encodeURIComponent(sessionId)}`,
    );
    const body = await response.json();

    if (!response.ok || !body.ok) {
      localStorage.removeItem(SESSION_KEY);
      sessionId = null;
      localMessages = [];
      renderSessionId();
      renderMessages();
      renderSessionListFromCache();
      showError(body.error, "加载历史失败。");
      return;
    }

    localMessages = body.data.history.filter((item) => item.role !== "system");
    renderMessages();
    renderSessionId();
    renderSessionListFromCache();
  } catch {
    showError("加载历史失败，请确认后端服务已启动。");
  }
}

async function loadSessionList(options = {}) {
  const { silent = false } = options;

  try {
    const response = await fetchWithRetry(`${API_BASE_URL}/sessions`);
    const body = await response.json();

    if (!response.ok || !body.ok) {
      if (!silent) {
        showError(body.error, "加载会话列表失败。");
      }
      return;
    }

    updateSessionList(body.data.sessions);

    if (!silent) {
      showToast("会话列表已刷新", "success");
    }
  } catch {
    if (!silent) {
      showError("加载会话列表失败，请确认后端服务已启动。");
    }
  }
}

function updateSessionList(sessions) {
  const snapshot = JSON.stringify({
    active: sessionId,
    sessions,
  });

  if (snapshot === sessionListSnapshot) {
    return;
  }

  sessionListSnapshot = snapshot;
  renderSessionList(sessions);
}

function renderSessionListFromCache() {
  if (!sessionListSnapshot) {
    return;
  }

  try {
    const cached = JSON.parse(sessionListSnapshot);
    sessionListSnapshot = "";
    updateSessionList(cached.sessions || []);
  } catch {
    sessionListSnapshot = "";
  }
}

function renderSessionList(sessions) {
  sessionListEl.replaceChildren();

  if (sessions.length === 0) {
    const emptyEl = document.createElement("div");
    emptyEl.className = "session-list-empty";
    emptyEl.textContent = "暂无历史会话";
    sessionListEl.appendChild(emptyEl);
    return;
  }

  for (const item of sessions) {
    const buttonEl = document.createElement("button");
    buttonEl.type = "button";
    buttonEl.className = "session-item";

    if (item.session_id === sessionId) {
      buttonEl.classList.add("session-item-active");
    }

    const titleEl = document.createElement("span");
    titleEl.className = "session-item-title";
    titleEl.textContent = getSessionTitle(item);

    const previewEl = document.createElement("span");
    previewEl.className = "session-item-preview";
    previewEl.textContent = getSessionPreview(item);

    const metaEl = document.createElement("span");
    metaEl.className = "session-item-meta";
    metaEl.textContent = `${item.message_count} 条消息`;

    buttonEl.appendChild(titleEl);
    buttonEl.appendChild(previewEl);
    buttonEl.appendChild(metaEl);

    buttonEl.addEventListener("click", async () => {
      if (item.session_id === sessionId) {
        return;
      }

      clearPendingDelete();
      sessionId = item.session_id;
      localStorage.setItem(SESSION_KEY, sessionId);
      renderSessionId();
      renderSessionListFromCache();
      await loadSavedSession();
      await loadSessionList({ silent: true });
    });

    sessionListEl.appendChild(buttonEl);
  }
}

async function deleteCurrentSession() {
  try {
    const deletedSessionId = sessionId;
    const response = await fetchWithRetry(
      `${API_BASE_URL}/sessions/${encodeURIComponent(deletedSessionId)}`,
      { method: "DELETE" },
    );
    const body = await response.json();

    if (!response.ok || !body.ok) {
      showError(body.error, "删除失败。");
      return;
    }

    clearPendingDelete();
    sessionId = null;
    localMessages = [];
    localStorage.removeItem(SESSION_KEY);
    renderSessionId();
    renderMessages();
    await loadSessionList({ silent: true });
    showToast("会话已删除", "success");
  } catch {
    showError("删除失败，请确认后端服务已启动。");
  }
}

async function streamChatMessage(message) {
  const payload = { message };

  if (sessionId) {
    payload.session_id = sessionId;
  }

  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok || !response.body) {
    throw new Error("stream request failed");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const part of parts) {
      handleSseMessage(part);
    }
  }

  if (buffer.trim()) {
    handleSseMessage(buffer);
  }
}

function handleSseMessage(rawMessage) {
  const lines = rawMessage.split("\n");
  let event = "message";
  let dataText = "";

  for (const line of lines) {
    if (line.startsWith("event: ")) {
      event = line.slice("event: ".length).trim();
      continue;
    }

    if (line.startsWith("data: ")) {
      dataText += line.slice("data: ".length);
    }
  }

  if (!dataText) {
    return;
  }

  const data = JSON.parse(dataText);

  if (event === "session") {
    sessionId = data.session_id;
    localStorage.setItem(SESSION_KEY, sessionId);
    renderSessionId();
    renderSessionListFromCache();
    return;
  }

  if (event === "chunk") {
    appendAssistantChunk(data.content || "");
    return;
  }

  if (event === "done") {
    sessionId = data.session_id;
    localStorage.setItem(SESSION_KEY, sessionId);
    renderSessionId();

    if (Array.isArray(data.history)) {
      localMessages = data.history.filter((item) => item.role !== "system");
      renderMessages();
    }

    loadSessionList({ silent: true });
    return;
  }

  if (event === "error") {
    removeThinkingMessages();
    removeEmptyAssistantDraft();
    showError(data, "SSE 请求失败。");
  }
}

function appendAssistantChunk(content) {
  if (!content) {
    return;
  }

  removeThinkingMessages({ render: false });

  let lastMessage = localMessages[localMessages.length - 1];

  if (!lastMessage || lastMessage.role !== "assistant") {
    lastMessage = {
      role: "assistant",
      content: "",
    };
    localMessages.push(lastMessage);
    streamAssistantContentEl = appendMessageElement(lastMessage);
  }

  lastMessage.content += content;
  updateLastMessageContent(lastMessage.content);
}

function appendMessage(role, content) {
  localMessages.push({ role, content });
  renderMessages();
}

function renderMessages() {
  streamAssistantContentEl = null;
  cancelPendingAssistantRender();
  messagesEl.replaceChildren();

  if (localMessages.length === 0) {
    const emptyEl = document.createElement("div");
    emptyEl.className = "empty-state";
    emptyEl.textContent = "开始一段对话";
    messagesEl.appendChild(emptyEl);
    return;
  }

  for (const message of localMessages) {
    appendMessageElement(message);
  }

  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function appendMessageElement(message) {
  const itemEl = document.createElement("article");
  itemEl.className = `message message-${message.role}`;

  const roleEl = document.createElement("div");
  roleEl.className = "message-role";
  roleEl.textContent = getRoleLabel(message.role);

  const contentEl = document.createElement("div");
  contentEl.className = "message-content";

  if (message.role === "thinking") {
    contentEl.appendChild(createThinkingIndicator());
  } else if (message.role === "assistant") {
    contentEl.innerHTML = renderMarkdown(message.content);
  } else {
    contentEl.textContent = message.content;
  }

  itemEl.appendChild(roleEl);
  itemEl.appendChild(contentEl);
  messagesEl.appendChild(itemEl);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  if (message.role === "assistant") {
    streamAssistantContentEl = contentEl;
  }

  return contentEl;
}

function updateLastMessageContent(content) {
  if (!streamAssistantContentEl || !streamAssistantContentEl.isConnected) {
    const assistantEls = messagesEl.querySelectorAll(
      ".message-assistant .message-content",
    );
    streamAssistantContentEl = assistantEls[assistantEls.length - 1] || null;
  }

  if (!streamAssistantContentEl) {
    renderMessages();
    return;
  }

  pendingAssistantContent = content;

  if (pendingAssistantFrame) {
    return;
  }

  pendingAssistantFrame = requestAnimationFrame(() => {
    pendingAssistantFrame = null;

    if (!streamAssistantContentEl || !streamAssistantContentEl.isConnected) {
      return;
    }

    streamAssistantContentEl.innerHTML = renderMarkdown(pendingAssistantContent);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  });
}

function createThinkingIndicator() {
  const wrapperEl = document.createElement("div");
  wrapperEl.className = "thinking-indicator";

  for (let index = 0; index < 3; index += 1) {
    const dotEl = document.createElement("span");
    dotEl.className = "thinking-dot";
    wrapperEl.appendChild(dotEl);
  }

  return wrapperEl;
}

function removeThinkingMessages(options = {}) {
  const { render = true } = options;
  localMessages = localMessages.filter((message) => message.role !== "thinking");

  if (render) {
    renderMessages();
    return;
  }

  for (const itemEl of messagesEl.querySelectorAll(".message-thinking")) {
    itemEl.remove();
  }
}

function removeEmptyAssistantDraft() {
  const lastMessage = localMessages[localMessages.length - 1];

  if (
    lastMessage &&
    lastMessage.role === "assistant" &&
    lastMessage.content === ""
  ) {
    localMessages.pop();
    renderMessages();
  }
}

function renderSessionId() {
  document.documentElement.dataset.sessionState = sessionId ? "active" : "empty";
}

function setLoading(isLoading) {
  sendButtonEl.disabled = isLoading;
  inputEl.disabled = isLoading;
  sendButtonEl.textContent = isLoading ? "发送中" : "发送";
}

function getRoleLabel(role) {
  if (role === "user") {
    return "你";
  }

  if (role === "assistant" || role === "thinking") {
    return "助手";
  }

  return "错误";
}

async function fetchWithRetry(url, options = {}, retries = 1) {
  try {
    return await fetch(url, options);
  } catch (error) {
    if (retries <= 0) {
      throw error;
    }

    await sleep(300);
    return fetchWithRetry(url, options, retries - 1);
  }
}

function showError(errorOrMessage, fallbackMessage = "请求失败。") {
  showToast(formatErrorMessage(errorOrMessage, fallbackMessage), "error");
}

function formatErrorMessage(errorOrMessage, fallbackMessage) {
  if (typeof errorOrMessage === "string") {
    return `请求失败：${errorOrMessage}`;
  }

  const message = errorOrMessage?.message || fallbackMessage;
  const requestId = errorOrMessage?.request_id;

  if (requestId) {
    return `请求失败：${message}（request_id: ${requestId}）`;
  }

  return `请求失败：${message}`;
}

function showToast(message, type = "info") {
  const toastEl = document.createElement("div");
  toastEl.className = `toast toast-${type}`;
  toastEl.setAttribute("role", "status");

  const markerEl = document.createElement("span");
  markerEl.className = "toast-marker";

  const textEl = document.createElement("span");
  textEl.className = "toast-message";
  textEl.textContent = message;

  toastEl.appendChild(markerEl);
  toastEl.appendChild(textEl);
  toastViewportEl.appendChild(toastEl);

  window.setTimeout(() => {
    toastEl.classList.add("toast-leaving");
  }, 3200);

  window.setTimeout(() => {
    toastEl.remove();
  }, 3800);
}

function clearPendingDelete() {
  pendingDeleteSessionId = null;
  window.clearTimeout(pendingDeleteTimer);
  deleteSessionButtonEl.textContent = "删除当前会话";
}

function getSessionTitle(item) {
  const title = String(item.title || "").trim();
  return title || "新会话";
}

function getSessionPreview(item) {
  return item.session_id || "未创建";
}

function cancelPendingAssistantRender() {
  if (!pendingAssistantFrame) {
    return;
  }

  cancelAnimationFrame(pendingAssistantFrame);
  pendingAssistantFrame = null;
}

function nextFrame() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      resolve();
    });
  });
}

function sleep(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function renderMarkdown(text) {
  const html = marked.parse(text || "");
  return DOMPurify.sanitize(html);
}
