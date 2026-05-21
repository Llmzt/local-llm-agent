import "./styles.css";

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

let sessionId = localStorage.getItem(SESSION_KEY);//读取浏览器存储的对话ID
let localMessages = [];

//刷新/初始化操作：
renderSessionId();//显示当前 session_id
renderMessages();//初始化历史聊天记录
checkHealth();//检查后端 API 是否能连接
loadSavedSession();


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

newSessionButtonEl.addEventListener("click", () => {//“新会话“按钮功能
  sessionId = null;//重置对话ID
  localMessages = [];//清空消息列表
  localStorage.removeItem(SESSION_KEY);//删除当前对话ID
  renderMessages();//重新渲染页面
  renderSessionId();
  inputEl.focus();//输入框重新聚焦
});

//将消息发送给后端
async function sendChatMessage(message) {
  const payload = {
    message,
  };

  if (sessionId) {
    payload.session_id = sessionId;
  }

  const response = await fetch(`${API_BASE_URL}/chat`, {
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
    const response = await fetch(`${API_BASE_URL}/health`);
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
    const response = await fetch(
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

  lastContentEl.textContent = content;
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

function renderMessages() {//根据 localMessages 重新画出聊天记录
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
    contentEl.textContent = message.content;
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