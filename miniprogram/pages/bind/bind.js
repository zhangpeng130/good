const api = require("../../services/api");

Page({
  data: {
    elderPhone: "",
    bindingCode: "",
    nickname: "",
    childPhone: "",
    loading: false,
  },
  onInput(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ [field]: e.detail.value });
  },
  getOpenid() {
    let openid = wx.getStorageSync("good_mock_openid");
    if (!openid) {
      openid = `mock_openid_${Date.now()}_${Math.random().toString(16).slice(2, 10)}`;
      wx.setStorageSync("good_mock_openid", openid);
    }
    return openid;
  },
  async onBind() {
    const { elderPhone, bindingCode, nickname, childPhone } = this.data;
    if (!/^1[3-9]\d{9}$/.test(elderPhone)) {
      wx.showToast({ title: "手机号不正确", icon: "none" });
      return;
    }
    if (!/^\d{6}$/.test(bindingCode)) {
      wx.showToast({ title: "绑定码不正确", icon: "none" });
      return;
    }
    if (childPhone && !/^1[3-9]\d{9}$/.test(childPhone)) {
      wx.showToast({ title: "联系电话不正确", icon: "none" });
      return;
    }

    this.setData({ loading: true });
    try {
      const data = await api.childBind({
        elderPhone,
        bindingCode,
        openid: this.getOpenid(),
        nickname: nickname || "子女",
        childPhone,
      });
      wx.setStorageSync("good_child_token", data.token);
      wx.setStorageSync("good_elder_id", data.elder.id);
      wx.setStorageSync("good_elder_name", data.elder.name || "爸爸");
      wx.showToast({ title: "绑定成功", icon: "success" });
      wx.redirectTo({ url: "/pages/dashboard/dashboard" });
    } catch (error) {
      wx.showToast({ title: error.message || "绑定失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
    }
  },
});

