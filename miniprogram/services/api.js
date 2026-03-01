const config = require("../config");

function getToken() {
  return wx.getStorageSync("good_child_token") || "";
}

function request(path, data = {}, auth = true) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${config.API_BASE}/${path}`,
      method: "POST",
      data,
      header: auth ? { Authorization: `Bearer ${getToken()}` } : {},
      success(res) {
        const payload = res.data || {};
        if (payload.code === 0) {
          resolve(payload.data);
          return;
        }
        reject(new Error(payload.message || "请求失败"));
      },
      fail(err) {
        reject(err);
      },
    });
  });
}

function childBind({ elderPhone, bindingCode, openid, nickname, childPhone }) {
  return request(
    "verify_login",
    {
      action: "child_bind",
      elder_phone: elderPhone,
      binding_code: bindingCode,
      openid,
      nickname,
      child_phone: childPhone || "",
    },
    false
  );
}

function getDashboard(elderId) {
  return request(
    "heartbeat",
    {
      action: "get_dashboard",
      elder_id: elderId,
    },
    true
  );
}

function unbind(elderId) {
  return request(
    "heartbeat",
    {
      action: "unbind",
      elder_id: elderId,
    },
    true
  );
}

module.exports = {
  childBind,
  getDashboard,
  unbind,
};

