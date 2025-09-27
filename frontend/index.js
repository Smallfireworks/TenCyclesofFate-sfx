// --- Constants ---
const API_BASE_URL = "/api";

// --- State Management ---
const appState = {
  gameState: null,
};

// --- DOM Elements ---
const DOMElements = {
  loginView: document.getElementById("login-view"),
  gameView: document.getElementById("game-view"),
  loginForm: document.getElementById("login-form"),
  loginError: document.getElementById("login-error"),
  loginButton: document.querySelector(".login-button"),
  statusToggle: document.getElementById("status-toggle"),
  statusFloat: document.getElementById("status-float"),
  logoutButton: document.getElementById("logout-button"),
  narrativeWindow: document.getElementById("narrative-window"),
  characterStatus: document.getElementById("character-status"),
  opportunitiesSpan: document.getElementById("opportunities"),
  actionInput: document.getElementById("action-input"),
  actionButton: document.getElementById("action-button"),
  startTrialButton: document.getElementById("start-trial-button"),
  refreshAttemptsButton: document.getElementById("refresh-attempts-button"),
  loadingSpinner: document.getElementById("loading-spinner"),
  rollOverlay: document.getElementById("roll-overlay"),
  rollPanel: document.getElementById("roll-panel"),
  rollType: document.getElementById("roll-type"),
  rollTarget: document.getElementById("roll-target"),
  rollResultDisplay: document.getElementById("roll-result-display"),
  rollOutcome: document.getElementById("roll-outcome"),
  rollValue: document.getElementById("roll-value"),
};

// --- API Client ---
const api = {
  async login(username, password) {
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    const response = await fetch(`${API_BASE_URL}/login`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Login failed" }));
      throw new Error(error.detail || "Login failed");
    }

    return response.json();
  },
  async initGame() {
    const response = await fetch(`${API_BASE_URL}/game/init`, {
      method: "POST",
      // No Authorization header needed, relies on HttpOnly cookie
    });
    if (response.status === 401) {
      throw new Error("Unauthorized");
    }
    if (!response.ok) throw new Error("Failed to initialize game session");
    return response.json();
  },
  async logout() {
    const response = await fetch(`${API_BASE_URL}/logout`, {
      method: "POST",
    });
    if (response.ok) {
      window.location.href = "/";
    }
  },
  async refreshAttempts() {
    const response = await fetch(`${API_BASE_URL}/game/refresh-attempts`, {
      method: "POST",
    });
    if (response.status === 401) {
      throw new Error("Unauthorized");
    }
    if (!response.ok) throw new Error("Failed to refresh attempts");
    return response.json();
  },
};

// --- WebSocket Manager ---
const socketManager = {
  socket: null,
  connect() {
    return new Promise((resolve, reject) => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = window.location.host;
      // The token is no longer in the URL; it's read from the cookie by the server.
      const wsUrl = `${protocol}//${host}${API_BASE_URL}/ws`;
      this.socket = new WebSocket(wsUrl);
      this.socket.binaryType = "arraybuffer"; // Important for receiving binary data

      this.socket.onopen = () => {
        console.log("WebSocket established.");
        resolve();
      };
      this.socket.onmessage = (event) => {
        let message;
        // Check if the data is binary (ArrayBuffer)
        if (event.data instanceof ArrayBuffer) {
          try {
            // Decompress the gzip data using pako.ungzip
            const decompressed = pako.ungzip(new Uint8Array(event.data), {
              to: "string",
            });
            message = JSON.parse(decompressed);
          } catch (err) {
            console.error("Failed to decompress or parse message:", err);
            return;
          }
        } else {
          // Fallback for non-binary messages
          message = JSON.parse(event.data);
        }

        switch (message.type) {
          case "full_state":
            appState.gameState = message.data;
            render();
            break;
          case "roll_event": // Listen for the separate, immediate roll event
            renderRollEvent(message.data);
            break;
          case "error":
            alert(`WebSocket Error: ${message.detail}`);
            break;
        }
      };
      this.socket.onclose = () => {
        console.log("Reconnecting...");
        showLoading(true);
        setTimeout(() => this.connect(), 5000);
      };
      this.socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        DOMElements.loginError.textContent = "无法连接。";
        reject(error);
      };
    });
  },
  sendAction(action) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ action }));
    } else {
      alert("连接已断开，请刷新。");
    }
  },
};
// Apply persisted sidebar state
const collapsed = localStorage.getItem("collapsedStatusPanel") === "1";
document
  .getElementById("game-view")
  .classList.toggle("collapsed-status", collapsed);

// Apply floating status panel state
const floatOn = localStorage.getItem("floatingStatusPanel") === "1";
const gv2 = DOMElements.gameView;
gv2.classList.toggle("floating-status", floatOn);
if (floatOn) {
  const panel = document.getElementById("status-panel");
  panel.classList.add("floating");
  const x = parseInt(localStorage.getItem("statusPanelLeft") || "20", 10);
  const y = parseInt(localStorage.getItem("statusPanelTop") || "80", 10);
  const w = parseInt(localStorage.getItem("statusPanelW") || "300", 10);
  const h = parseInt(localStorage.getItem("statusPanelH") || "360", 10);
  panel.style.left = x + "px";
  panel.style.top = y + "px";
  panel.style.width = w + "px";
  panel.style.height = h + "px";
}

// --- UI & Rendering ---
function showView(viewId) {
  document
    .querySelectorAll(".view")
    .forEach((v) => v.classList.remove("active"));
  document.getElementById(viewId).classList.add("active");
}
// Setup status panel UI (toggle, float, drag, resize, snap)
function setupStatusPanelUI() {
  if (window.__statusPanelUISetup) return;
  window.__statusPanelUISetup = true;
  const gv = DOMElements.gameView;
  const panel = document.getElementById("status-panel");
  if (!panel) return;

  // Collapse/expand entire panel
  if (DOMElements.statusToggle) {
    DOMElements.statusToggle.addEventListener("click", () => {
      const now = !gv.classList.contains("collapsed-status");
      gv.classList.toggle("collapsed-status", now);
      localStorage.setItem("collapsedStatusPanel", now ? "1" : "0");
    });
  }

  // Helper: ensure resizer handle exists
  function ensureResizer() {
    if (panel.querySelector(".resizer")) return;
    const resizer = document.createElement("div");
    resizer.className = "resizer";
    panel.appendChild(resizer);

    let resizing = false;
    let startX = 0,
      startY = 0;
    let startW = 0,
      startH = 0;
    resizer.addEventListener("mousedown", (e) => {
      if (!panel.classList.contains("floating")) return;
      e.stopPropagation();
      resizing = true;
      const rect = panel.getBoundingClientRect();
      startX = e.clientX;
      startY = e.clientY;
      startW = rect.width;
      startH = rect.height;
      document.body.style.userSelect = "none";
    });
    window.addEventListener("mousemove", (e) => {
      if (!resizing) return;
      const minW = 220,
        minH = 160;
      const newW = Math.max(minW, startW + (e.clientX - startX));
      const newH = Math.max(minH, startH + (e.clientY - startY));
      panel.style.width = newW + "px";
      panel.style.maxHeight = "none";
      panel.style.height = newH + "px";
    });
    window.addEventListener("mouseup", () => {
      if (!resizing) return;
      resizing = false;
      document.body.style.userSelect = "";
      localStorage.setItem(
        "statusPanelW",
        String(parseInt(panel.style.width || "300", 10))
      );
      localStorage.setItem(
        "statusPanelH",
        String(parseInt(panel.style.height || "300", 10))
      );
    });
  }

  // Float/dock toggle
  if (DOMElements.statusFloat) {
    DOMElements.statusFloat.addEventListener("click", () => {
      const now = !panel.classList.contains("floating");
      panel.classList.toggle("floating", now);
      gv.classList.toggle("floating-status", now);
      localStorage.setItem("floatingStatusPanel", now ? "1" : "0");
      if (now) {
        // restore defaults/last
        panel.style.left =
          (localStorage.getItem("statusPanelLeft") || "20") + "px";
        panel.style.top =
          (localStorage.getItem("statusPanelTop") || "80") + "px";
        const w = parseInt(localStorage.getItem("statusPanelW") || "300", 10);
        const h = parseInt(localStorage.getItem("statusPanelH") || "360", 10);
        panel.style.width = w + "px";
        panel.style.height = h + "px";
        ensureResizer();
      } else {
        panel.style.left =
          panel.style.top =
          panel.style.width =
          panel.style.height =
            "";
      }
    });
  }

  // Dragging (skip when grabbing resizer)
  let dragging = false;
  let offsetX = 0,
    offsetY = 0;
  panel.addEventListener("mousedown", (e) => {
    if (!panel.classList.contains("floating")) return;
    if (e.target.classList && e.target.classList.contains("resizer")) return;
    dragging = true;
    const rect = panel.getBoundingClientRect();
    offsetX = e.clientX - rect.left;
    offsetY = e.clientY - rect.top;
    document.body.style.userSelect = "none";
  });
  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    const x = Math.max(
      0,
      Math.min(window.innerWidth - 100, e.clientX - offsetX)
    );
    const y = Math.max(
      0,
      Math.min(window.innerHeight - 100, e.clientY - offsetY)
    );
    panel.style.left = x + "px";
    panel.style.top = y + "px";
  });
  window.addEventListener("mouseup", () => {
    if (!dragging) return;
    dragging = false;
    document.body.style.userSelect = "";
    // edge snapping
    const rect = panel.getBoundingClientRect();
    const margin = 20,
      snapT = 24;
    let left = rect.left,
      top = rect.top;
    if (rect.left <= snapT) left = margin;
    if (window.innerWidth - rect.right <= snapT)
      left = window.innerWidth - rect.width - margin;
    if (rect.top <= snapT) top = margin;
    if (window.innerHeight - rect.bottom <= snapT)
      top = window.innerHeight - rect.height - margin;
    panel.style.left = Math.max(0, Math.floor(left)) + "px";
    panel.style.top = Math.max(0, Math.floor(top)) + "px";
    localStorage.setItem(
      "statusPanelLeft",
      String(parseInt(panel.style.left, 10))
    );
    localStorage.setItem(
      "statusPanelTop",
      String(parseInt(panel.style.top, 10))
    );
  });
}

function showLoading(isLoading) {
  DOMElements.loadingSpinner.style.display = isLoading ? "flex" : "none";
  const isProcessing = appState.gameState
    ? appState.gameState.is_processing
    : false;
  const buttonsDisabled = isLoading || isProcessing;
  // DOMElements.loginButton is removed
  DOMElements.actionInput.disabled = buttonsDisabled;
  DOMElements.actionButton.disabled = buttonsDisabled;
  DOMElements.startTrialButton.disabled = buttonsDisabled;
}

function render() {
  if (!appState.gameState) {
    showLoading(true);
    return;
  }
  showLoading(appState.gameState.is_processing);
  DOMElements.opportunitiesSpan.textContent =
    appState.gameState.opportunities_remaining;
  renderCharacterStatus();

  const historyContainer = document.createDocumentFragment();
  (appState.gameState.display_history || []).forEach((text) => {
    const p = document.createElement("div");
    p.innerHTML = marked.parse(text);
    if (text.startsWith("> ")) p.classList.add("user-input-message");
    else if (text.startsWith("【")) p.classList.add("system-message");
    historyContainer.appendChild(p);
  });
  DOMElements.narrativeWindow.innerHTML = "";
  DOMElements.narrativeWindow.appendChild(historyContainer);
  DOMElements.narrativeWindow.scrollTop =
    DOMElements.narrativeWindow.scrollHeight;

  const { is_in_trial, daily_success_achieved, opportunities_remaining } =
    appState.gameState;
  DOMElements.actionInput.parentElement.classList.toggle(
    "hidden",
    !(is_in_trial || daily_success_achieved || opportunities_remaining < 0)
  );
  const startButton = DOMElements.startTrialButton;
  startButton.classList.toggle(
    "hidden",
    is_in_trial || daily_success_achieved || opportunities_remaining < 0
  );

  // Show refresh attempts button when daily success is achieved (破碎虚空)
  const refreshButton = DOMElements.refreshAttemptsButton;
  refreshButton.classList.toggle("hidden", !daily_success_achieved);

  if (daily_success_achieved) {
    startButton.textContent = "今日功德圆满";
    startButton.disabled = true;
  } else if (opportunities_remaining <= 0) {
    startButton.textContent = "机缘已尽";
    startButton.disabled = true;
  } else {
    if (opportunities_remaining === 10) {
      startButton.textContent = "开始第一次试炼";
    } else {
      startButton.textContent = "开启下一次试炼";
    }
    startButton.disabled = appState.gameState.is_processing;
  }
}

function renderValue(container, value, level = 0) {
  if (Array.isArray(value)) {
    value.forEach((item) => renderValue(container, item, level + 1));
  } else if (typeof value === "object" && value !== null) {
    const subContainer = document.createElement("div");
    subContainer.style.paddingLeft = `${level * 10}px`;
    Object.entries(value).forEach(([key, val]) => {
      const propDiv = document.createElement("div");
      propDiv.classList.add("property-item");

      const keySpan = document.createElement("span");
      keySpan.classList.add("property-key");
      keySpan.textContent = `${key}: `;
      propDiv.appendChild(keySpan);

      // Recursively render the value
      renderValue(propDiv, val, level + 1);
      subContainer.appendChild(propDiv);
    });
    container.appendChild(subContainer);
  } else {
    const valueSpan = document.createElement("span");
    valueSpan.classList.add("property-value");
    valueSpan.textContent = value;
    container.appendChild(valueSpan);
  }
}

function renderCharacterStatus() {
  const { current_life } = appState.gameState;
  const container = DOMElements.characterStatus;
  container.innerHTML = ""; // Clear previous content

  if (!current_life) {
    container.textContent = "静待天命...";
    return;
  }

  Object.entries(current_life).forEach(([key, value]) => {
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = key;
    details.appendChild(summary);

    const content = document.createElement("div");
    content.classList.add("details-content");

    renderValue(content, value);

    details.appendChild(content);
    container.appendChild(details);
  });
}

function renderRollEvent(rollEvent) {
  DOMElements.rollType.textContent = `判定: ${rollEvent.type}`;
  DOMElements.rollTarget.textContent = `(<= ${rollEvent.target})`;
  DOMElements.rollOutcome.textContent = rollEvent.outcome;
  DOMElements.rollOutcome.className = `outcome-${rollEvent.outcome}`;
  DOMElements.rollValue.textContent = rollEvent.result;
  DOMElements.rollResultDisplay.classList.add("hidden");
  DOMElements.rollOverlay.classList.remove("hidden");
  setTimeout(
    () => DOMElements.rollResultDisplay.classList.remove("hidden"),
    1000
  );
  setTimeout(() => DOMElements.rollOverlay.classList.add("hidden"), 3000);
}

// --- Event Handlers ---
async function handleLogin(event) {
  event.preventDefault();

  const formData = new FormData(event.target);
  const username = formData.get("username");
  const password = formData.get("password");

  if (!username || !password) {
    if (DOMElements.loginButton) DOMElements.loginButton.disabled = true;

    DOMElements.loginError.textContent = "请输入用户名和密码";
    return;
  }

  if (username.trim().length < 3 || password.trim().length < 3) {
    DOMElements.loginError.textContent = "用户名和密码至少3个字符";
    return;
  }

  try {
    DOMElements.loginError.textContent = "";
    showLoading(true);

    await api.login(username, password);

    // Login successful, initialize game
    if (DOMElements.loginButton) DOMElements.loginButton.disabled = false;

    await initializeGame();
  } catch (error) {
    console.error("Login error:", error);
    DOMElements.loginError.textContent = error.message || "登录失败";
  } finally {
    showLoading(false);
  }
}

function handleLogout() {
  api.logout();
}

async function handleRefreshAttempts() {
  if (!confirm("确定要重新开始今日试炼吗？这将重置所有进度。")) {
    return;
  }

  try {
    showLoading(true);
    const gameState = await api.refreshAttempts();
    appState.gameState = gameState;
    render();
  } catch (error) {
    console.error("Refresh attempts error:", error);
    alert("重新开始失败: " + (error.message || "未知错误"));
  } finally {
    showLoading(false);
  }
}

function handleAction(actionOverride = null) {
  const action = actionOverride || DOMElements.actionInput.value.trim();
  if (!action) return;

  // Special case for starting a trial to prevent getting locked out by is_processing flag
  if (action === "开始试炼") {
    // Allow starting a new trial even if the previous async task is in its finally block
    // Setup status panel UI (toggle, float, drag, resize, snap)
    function setupStatusPanelUI() {
      if (window.__statusPanelUISetup) return;
      window.__statusPanelUISetup = true;
      const gv = DOMElements.gameView;
      const panel = document.getElementById("status-panel");
      if (!panel) return;

      // Collapse/expand entire panel
      if (DOMElements.statusToggle) {
        DOMElements.statusToggle.addEventListener("click", () => {
          const now = !gv.classList.contains("collapsed-status");
          gv.classList.toggle("collapsed-status", now);
          localStorage.setItem("collapsedStatusPanel", now ? "1" : "0");
        });
      }

      // Helper: ensure resizer handle exists
      function ensureResizer() {
        if (panel.querySelector(".resizer")) return;
        const resizer = document.createElement("div");
        resizer.className = "resizer";
        panel.appendChild(resizer);

        let resizing = false;
        let startX = 0,
          startY = 0;
        let startW = 0,
          startH = 0;
        resizer.addEventListener("mousedown", (e) => {
          if (!panel.classList.contains("floating")) return;
          e.stopPropagation();
          resizing = true;
          const rect = panel.getBoundingClientRect();
          startX = e.clientX;
          startY = e.clientY;
          startW = rect.width;
          startH = rect.height;
          document.body.style.userSelect = "none";
        });
        window.addEventListener("mousemove", (e) => {
          if (!resizing) return;
          const minW = 220,
            minH = 160;
          const newW = Math.max(minW, startW + (e.clientX - startX));
          const newH = Math.max(minH, startH + (e.clientY - startY));
          panel.style.width = newW + "px";
          panel.style.maxHeight = "none";
          panel.style.height = newH + "px";
        });
        window.addEventListener("mouseup", () => {
          if (!resizing) return;
          resizing = false;
          document.body.style.userSelect = "";
          localStorage.setItem(
            "statusPanelW",
            String(parseInt(panel.style.width || "300", 10))
          );
          localStorage.setItem(
            "statusPanelH",
            String(parseInt(panel.style.height || "300", 10))
          );
        });
      }

      // Float/dock toggle
      if (DOMElements.statusFloat) {
        DOMElements.statusFloat.addEventListener("click", () => {
          const now = !panel.classList.contains("floating");
          panel.classList.toggle("floating", now);
          gv.classList.toggle("floating-status", now);
          localStorage.setItem("floatingStatusPanel", now ? "1" : "0");
          if (now) {
            // restore defaults/last
            panel.style.left =
              (localStorage.getItem("statusPanelLeft") || "20") + "px";
            panel.style.top =
              (localStorage.getItem("statusPanelTop") || "80") + "px";
            const w = parseInt(
              localStorage.getItem("statusPanelW") || "300",
              10
            );
            const h = parseInt(
              localStorage.getItem("statusPanelH") || "360",
              10
            );
            panel.style.width = w + "px";
            panel.style.height = h + "px";
            ensureResizer();
          } else {
            panel.style.left =
              panel.style.top =
              panel.style.width =
              panel.style.height =
                "";
          }
        });
      }

      // Dragging (skip when grabbing resizer)
      let dragging = false;
      let offsetX = 0,
        offsetY = 0;
      panel.addEventListener("mousedown", (e) => {
        if (!panel.classList.contains("floating")) return;
        if (e.target.classList && e.target.classList.contains("resizer"))
          return;
        dragging = true;
        const rect = panel.getBoundingClientRect();
        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;
        document.body.style.userSelect = "none";
      });
      window.addEventListener("mousemove", (e) => {
        if (!dragging) return;
        const x = Math.max(
          0,
          Math.min(window.innerWidth - 100, e.clientX - offsetX)
        );
        const y = Math.max(
          0,
          Math.min(window.innerHeight - 100, e.clientY - offsetY)
        );
        panel.style.left = x + "px";
        panel.style.top = y + "px";
      });
      window.addEventListener("mouseup", () => {
        if (!dragging) return;
        dragging = false;
        document.body.style.userSelect = "";
        // edge snapping
        const rect = panel.getBoundingClientRect();
        const margin = 20,
          snapT = 24;
        let left = rect.left,
          top = rect.top;
        if (rect.left <= snapT) left = margin;
        if (window.innerWidth - rect.right <= snapT)
          left = window.innerWidth - rect.width - margin;
        if (rect.top <= snapT) top = margin;
        if (window.innerHeight - rect.bottom <= snapT)
          top = window.innerHeight - rect.height - margin;
        panel.style.left = Math.max(0, Math.floor(left)) + "px";
        panel.style.top = Math.max(0, Math.floor(top)) + "px";
        localStorage.setItem(
          "statusPanelLeft",
          String(parseInt(panel.style.left, 10))
        );
        localStorage.setItem(
          "statusPanelTop",
          String(parseInt(panel.style.top, 10))
        );
      });
    }
  } else {
    // For all other actions, prevent sending if another action is in flight.
    if (appState.gameState && appState.gameState.is_processing) return;
  }

  DOMElements.actionInput.value = "";
  socketManager.sendAction(action);
}

// --- Initialization ---
async function initializeGame() {
  showLoading(true);
  try {
    const initialState = await api.initGame();
    appState.gameState = initialState;
    render();
    showView("game-view");
    await socketManager.connect();
    console.log("Initialization complete and WebSocket is ready.");
  } catch (error) {
    // If init fails (e.g. no valid cookie), just show the login view.
    // The api.initGame function no longer redirects, it just throws an error.
    showView("login-view");
    if (error.message !== "Unauthorized") {
      console.error(`Session initialization failed: ${error.message}`);
    }
    if (DOMElements.statusToggle) {
      DOMElements.statusToggle.addEventListener("click", () => {
        const gv = DOMElements.gameView;
        const now = !gv.classList.contains("collapsed-status");
        gv.classList.toggle("collapsed-status", now);
        localStorage.setItem("collapsedStatusPanel", now ? "1" : "0");
      });
    }

    // QoL: '/' focuses the action input
    window.addEventListener("keydown", (e) => {
      if (e.key === "/" && DOMElements.gameView.classList.contains("active")) {
        e.preventDefault();
        DOMElements.actionInput.focus();
      }
    });
  } finally {
    // Ensure spinner is hidden regardless of outcome
    showLoading(false);
  }
}

function init() {
  // Always try to initialize the game on page load.
  // If the user is logged in, it will show the game view.
  // If not, the catch block in initializeGame will handle showing the login view.
  initializeGame();
  // UI wiring independent of login state
  setupStatusPanelUI();

  // QoL: '/' focuses the action input when in game view
  window.addEventListener("keydown", (e) => {
    if (e.key === "/" && DOMElements.gameView.classList.contains("active")) {
      e.preventDefault();
      DOMElements.actionInput.focus();
    }
  });

  // Setup event listeners regardless of initial view
  DOMElements.loginForm.addEventListener("submit", handleLogin);
  DOMElements.logoutButton.addEventListener("click", handleLogout);
  DOMElements.actionButton.addEventListener("click", () => handleAction());
  DOMElements.actionInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleAction();
  });
  DOMElements.startTrialButton.addEventListener("click", () =>
    handleAction("开始试炼")
  );
  DOMElements.refreshAttemptsButton.addEventListener(
    "click",
    handleRefreshAttempts
  );
}

// --- Start the App ---
init();
