const API_BASE = import.meta.env.VITE_API_BASE || "";

function getToken() {
  return uni.getStorageSync("good_token") || "";
}

function request(path, data = {}, auth = true) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}/${path}`,
      method: "POST",
      data,
      header: auth
        ? {
            Authorization: `Bearer ${getToken()}`,
          }
        : {},
      success: (res) => {
        const payload = res.data || {};
        if (payload.code === 0) {
          resolve(payload.data);
          return;
        }
        reject(new Error(payload.message || "请求失败"));
      },
      fail: (err) => reject(err),
    });
  });
}

export function sendCode(phone, readAloud = false) {
  return request(
    "send_code",
    {
      phone,
      purpose: "elder_login",
      read_aloud: readAloud,
    },
    false
  );
}

export function elderLogin(phone, code) {
  return request(
    "verify_login",
    {
      action: "elder_login",
      phone,
      code,
    },
    false
  );
}

export function heartbeat(action = "heartbeat", payload = {}) {
  return request("heartbeat", { action, ...payload }, true);
}

export function triggerSos(payload = {}) {
  return request("trigger_sos", payload, true);
}

