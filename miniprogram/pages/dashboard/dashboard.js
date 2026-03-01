const api = require("../../services/api");

function formatDate(value) {
  if (!value) return "暂无";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return "暂无";
  const y = dt.getFullYear();
  const m = `${dt.getMonth() + 1}`.padStart(2, "0");
  const d = `${dt.getDate()}`.padStart(2, "0");
  const hh = `${dt.getHours()}`.padStart(2, "0");
  const mm = `${dt.getMinutes()}`.padStart(2, "0");
  return `${y}-${m}-${d} ${hh}:${mm}`;
}

Page({
  data: {
    elderId: 0,
    elderName: "爸爸",
    statusLabel: "⚪ 离线",
    statusClass: "offline",
    lastCheckinText: "暂无",
    sosList: [],
    loading: false,
  },
  onShow() {
    const elderId = Number(wx.getStorageSync("good_elder_id") || 0);
    const elderName = wx.getStorageSync("good_elder_name") || "爸爸";
    this.setData({ elderId, elderName });
    if (!elderId) {
      wx.redirectTo({ url: "/pages/bind/bind" });
      return;
    }
    this.fetchDashboard();
  },
  async fetchDashboard() {
    const { elderId } = this.data;
    this.setData({ loading: true });
    try {
      const dashboard = await api.getDashboard(elderId);
      const elder = dashboard.elder || {};
      const sosList = (dashboard.recent_sos || []).map((item) => ({
        ...item,
        created_at_text: formatDate(item.created_at),
        address_text: item.address || "未知位置",
      }));
      this.setData({
        statusLabel: dashboard.status === "online" ? "🟢 在线" : "⚪ 离线",
        statusClass: dashboard.status === "online" ? "online" : "offline",
        lastCheckinText: formatDate(elder.last_checkin_at),
        sosList,
      });
    } catch (error) {
      wx.showToast({ title: error.message || "获取看板失败", icon: "none" });
    } finally {
      this.setData({ loading: false });
    }
  },
  onUnbind() {
    wx.showModal({
      title: "确认解绑",
      content: "解绑后将无法继续接收守护通知",
      success: async (res) => {
        if (!res.confirm) return;
        try {
          await api.unbind(this.data.elderId);
          wx.removeStorageSync("good_child_token");
          wx.removeStorageSync("good_elder_id");
          wx.removeStorageSync("good_elder_name");
          wx.showToast({ title: "已解绑", icon: "success" });
          wx.redirectTo({ url: "/pages/bind/bind" });
        } catch (error) {
          wx.showToast({ title: error.message || "解绑失败", icon: "none" });
        }
      },
    });
  },
});

