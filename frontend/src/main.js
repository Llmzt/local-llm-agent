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

renderSessionId();//显示当前 session_id
checkHealth();//检查后端 API 是否能连接

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();//组织浏览器默认提交行为，防止每次提交表单都自动刷新

  const text = inputEl.value.trim();
  if (!text) {
    return;
  }

  inputEl.value = "";
  appendMessage("user", text);//将用户输入显示在页面上
  setLoading(true);//进入加载，防止用户重复提交

  try {
    const body = await sendChatMessage(text);//发送给后端

    if (!body.ok) {//处理后端的失败响应(能连接但后端报错)
      appendMessage("error", body.error?.message || "请求失败。");
      return;
    }

    const data = body.data;
    sessionId = data.session_id;
    localStorage.setItem(SESSION_KEY, sessionId);//保存对话ID（刷新后仍存在,但目前刷新后必须得发送一条信息才能显示历史对话）

    localMessages = data.history.filter((item) => item.role !== "system");//过滤系统提示词
    renderMessages();//程序渲染聊天区
    renderSessionId();//重新显示对话ID
  } catch (error) {//无法连接后端
    appendMessage("error", "无法连接 API，请确认后端服务已启动。");
  } finally {//无论请求成功还是失败,都恢复按钮和输入框,然后让输入框重新获得焦点
    setLoading(false);
    inputEl.focus();
  }
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

function appendMessage(role, content) {
  localMessages.push({ role, content });
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
    contentEl.textContent = message.content;

    itemEl.appendChild(roleEl);
    itemEl.appendChild(contentEl);
    messagesEl.appendChild(itemEl);
  }

  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function renderSessionId() {
  sessionIdEl.textContent = sessionId || "未创建";
}

function setLoading(isLoading) {//加载状态
  sendButtonEl.disabled = isLoading;
  inputEl.disabled = isLoading;
  sendButtonEl.textContent = isLoading ? "发送中" : "发送";
}

function getRoleLabel(role) {//将后端角色名改为页面文字
  if (role === "user") {
    return "你";
  }

  if (role === "assistant") {
    return "助手";
  }

  return "错误";
}