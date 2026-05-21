
import "./styles.css";
import { marked } from "marked";
import DOMPurify from "dompurify";

const API_BASE_URL = "http://127.0.0.1:8000";
const SESSION_KEY = "agent1.session_id";

//获取变量元素，以便后续操作
const messagesEl = document.querySelector("#messages");
const formEl = document.querySelector("#chatForm");
const inputEl = document.querySelector("#messageInput");
const sendButtonEl = document.querySelector("#sendButton");
const newSessionButtonEl = document.querySelector("#newSessionButton");
const sessionIdEl = document.querySelector("#sessionId");
const apiStatusEl = document.querySelector("#apiStatus");
//DOM引用
const refreshSessionsButtonEl = document.querySelector("#refreshSessionsButton");
const deleteSessionButtonEl = document.querySelector("#deleteSessionButton");
const sessionListEl = document.querySelector("#sessionList");

let sessionId = localStorage.getItem(SESSION_KEY);//读取浏览器存储的对话ID
let localMessages = [];

//刷新/初始化操作：
renderSessionId();//显示当前 session_id
renderMessages();//初始化历史聊天记录
checkHealth();//检查后端 API 是否能连接
loadSavedSession();
loadSessionList();//加载对话列表


formEl.addEventListener("submit", async (event) => {
  event.preventDefault();//组织浏览器默认提交行为，防止每次提交表单都自动刷新

  const text = inputEl.value.trim();//获取输入，去掉收尾空格
  if (!text) {
    return;
  }

  inputEl.value = "";
  appendMessage("user", text);//将用户输入显示在页面上
  appendMessage("thinking", "");
  setLoading(true);//进入加载，防止用户重复提交

  try {
    const body = await sendChatMessage(text);//发送给后端

    removeThinkingMessages();

    if (!body.ok) {//处理后端的失败响应(能连接但后端报错)
      appendMessage("error", body.error?.message || "请求失败。");
      return;
    }

    const data = body.data;
    sessionId = data.session_id;
    localStorage.setItem(SESSION_KEY, sessionId);//保存对话ID

    await renderHistoryWithStreamingReply(data.history);
    renderSessionId()//重新显示对话ID
  } catch (error) {//无法连接后端
    removeThinkingMessages();
    appendMessage("error", "无法连接 API，请确认后端服务已启动。");
  } finally {//无论请求成功还是失败,都恢复按钮和输入框,然后让输入框重新获得焦点
    setLoading(false);
    inputEl.focus();
  }
});

inputEl.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") {
    return;
  }

  if (event.shiftKey) {
    return;
  }

  event.preventDefault();

  if (sendButtonEl.disabled) {
    return;
  }

  formEl.requestSubmit();
});

//将消息发送给后端
async function sendChatMessage(message) {
  const payload = {
    message,
  };

  if (sessionId) {
    payload.session_id = sessionId;
  }

  const response = await fetchWithRetry(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return response.json();
}

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
  } catch {
    apiStatusEl.textContent = "未连接";
    apiStatusEl.dataset.state = "error";
  }
}

async function loadSavedSession() {//自动加载历史对话
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
      return;
    }

    localMessages = body.data.history.filter((item) => item.role !== "system");
    renderMessages();
    renderSessionId();
  } catch {
    appendMessage("error", "无法加载历史会话，请确认后端服务已启动。");
  }
}

function appendMessage(role, content) {
  localMessages.push({ role, content });
  renderMessages();
}

async function renderHistoryWithStreamingReply(history) {//逐字渲染
  const visibleHistory = history.filter((item) => item.role !== "system");//利用filter从消息里筛出系统消息外的消息

  if (visibleHistory.length === 0) {
    localMessages = [];
    renderMessages();
    return;
  }

  const lastMessage = visibleHistory[visibleHistory.length - 1];

  if (lastMessage.role !== "assistant") {
    localMessages = visibleHistory;
    renderMessages();
    return;
  }

  const fullReply = lastMessage.content;
  const messagesBeforeReply = visibleHistory.slice(0, -1);

  localMessages = [
    ...messagesBeforeReply,
    {
      role: "assistant",
      content: "",
    },
  ];
  renderMessages();

  await typeAssistantReply(fullReply);
}

async function typeAssistantReply(fullReply) {
  const lastIndex = localMessages.length - 1;

  for (const char of fullReply) {
    localMessages[lastIndex].content += char;
    updateLastMessageContent(localMessages[lastIndex].content);
    await sleep(8);
  }
}

function updateLastMessageContent(content) {
  const contentEls = messagesEl.querySelectorAll(".message-content");
  const lastContentEl = contentEls[contentEls.length - 1];

  if (!lastContentEl) {
    renderMessages();
    return;
  }

  lastContentEl.innerHTML = renderMarkdown(content);//markdown渲染
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function sleep(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function removeThinkingMessages() {
  localMessages = localMessages.filter((message) => message.role !== "thinking");
  renderMessages();
}

function renderMessages() {//对话渲染
  messagesEl.innerHTML = "";//清空原有消息

  if (localMessages.length === 0) {
    const emptyEl = document.createElement("div");
    emptyEl.className = "empty-state";//没有消息时
    emptyEl.textContent = "开始一段对话";//无对话消息时页面文字
    messagesEl.appendChild(emptyEl);
    return;
  }

  for (const message of localMessages) {//如果有消息，将local message循环创建为HTML元素
    const itemEl = document.createElement("article");
    itemEl.className = `message message-${message.role}`;

    const roleEl = document.createElement("div");
    roleEl.className = "message-role";
    roleEl.textContent = getRoleLabel(message.role);

    const contentEl = document.createElement("div");
    contentEl.className = "message-content";

    if (message.role === "thinking") {
    contentEl.appendChild(createThinkingIndicator());
    } else {
    if (message.role === "assistant") {
    contentEl.innerHTML = renderMarkdown(message.content);//对助手消息进行markdown渲染
                                                          //用户消息不渲染，防止执行用户输入进行XSS注入
    } else {
    contentEl.textContent = message.content;
    }
    }

    itemEl.appendChild(roleEl);
    itemEl.appendChild(contentEl);
    messagesEl.appendChild(itemEl);
  }

  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function createThinkingIndicator() {
  const wrapperEl = document.createElement("div");
  wrapperEl.className = "thinking-indicator";

  const dotEl = document.createElement("span");
  dotEl.className = "thinking-dot";

  wrapperEl.appendChild(dotEl);
  return wrapperEl;
}

function renderSessionId() {
  sessionIdEl.textContent = sessionId || "未创建";
}

function setLoading(isLoading) {//加载状态
  sendButtonEl.disabled = isLoading;
  inputEl.disabled = isLoading;
  sendButtonEl.textContent = isLoading ? "发送中" : "发送";
}

function getRoleLabel(role) {
  if (role === "user") {
    return "你";
  }

  if (role === "assistant") {
    return "助手";
  }

  if (role === "thinking") {
    return "助手";
  }

  return "错误";
}

//---------------------对话列表-----------------------
async function loadSessionList() {
  try {
    const response = await fetchWithRetry(`${API_BASE_URL}/sessions`);
    const body = await response.json();

    if (!response.ok || !body.ok) {
      showError(body.error?.message || "加载会话列表失败。");
      return;
    }

    renderSessionList(body.data.sessions);
  } catch {
    showError("无法加载会话列表，请确认后端服务已启动。");
  }
}

function renderSessionList(sessions) {
  sessionListEl.innerHTML = "";

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

    buttonEl.innerHTML = `
      <span class="session-item-title"></span>
      <span class="session-item-meta">${item.message_count} 条消息</span>
    `;

    buttonEl.querySelector(".session-item-title").textContent = item.title;

    buttonEl.addEventListener("click", async () => {
      sessionId = item.session_id;
      localStorage.setItem(SESSION_KEY, sessionId);
      renderSessionId();
      await loadSavedSession();
      await loadSessionList();
    });

    sessionListEl.appendChild(buttonEl);
  }
}

//-----------------------删除对话---------------------
deleteSessionButtonEl.addEventListener("click", async () => {
  if (!sessionId) {
    showError("当前没有可删除的会话。");
    return;
  }

  const shouldDelete = window.confirm("确定删除当前会话吗？");
  if (!shouldDelete) {
    return;
  }

  try {
    const response = await fetchWithRetry(
      `${API_BASE_URL}/sessions/${encodeURIComponent(sessionId)}`,
      { method: "DELETE" },
    );
    const body = await response.json();

    if (!response.ok || !body.ok) {
      showError(body.error?.message || "删除会话失败。");
      return;
    }

    sessionId = null;
    localMessages = [];
    localStorage.removeItem(SESSION_KEY);
    renderSessionId();
    renderMessages();
    await loadSessionList();
  } catch {
    showError("无法删除会话，请确认后端服务已启动。");
  }
});


refreshSessionsButtonEl.addEventListener("click", () => {
  loadSessionList();
});

//新对话按钮也加入刷新
newSessionButtonEl.addEventListener("click", () => {
  sessionId = null;
  localMessages = [];
  localStorage.removeItem(SESSION_KEY);
  renderMessages();
  renderSessionId();
  loadSessionList();
  inputEl.focus();
});

//api重试的fetch
async function fetchWithRetry(url, options = {}, retries = 1) {
  try {
    return await fetch(url, options);
  } catch (error) {
    if (retries <= 0) {
      throw error;
    }

    await sleep(300);
    return fetchWithRetry(url, options, retries - 1);//递归重试
  }
}

function renderMarkdown(text) {//markdown渲染
  const html = marked.parse(text || "");
  return DOMPurify.sanitize(html);
}

//错误提示函数
function showError(message) {
  appendMessage("error", message);
}
