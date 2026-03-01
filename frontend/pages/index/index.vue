<template>
  <view class="page">
    <view class="head">
      <text class="title">您好，{{ elderName }}</text>
      <text class="desc">点击绿色按钮报平安；长按 3 秒触发 SOS</text>
      <text class="bind-code">绑定码：{{ bindingCode }}</text>
    </view>

    <button
      class="safe-btn"
      @click="handleCheckin"
      @touchstart="startLongPress"
      @touchend="cancelLongPress"
      @touchcancel="cancelLongPress"
    >
      我很好
    </button>

    <text class="status">{{ statusText }}</text>
  </view>
</template>

<script>
import { heartbeat, triggerSos } from "../../utils/api";

export default {
  data() {
    return {
      elderName: "爸爸",
      bindingCode: "",
      statusText: "守护已开启",
      longPressTimer: null,
      heartbeatTimer: null,
      busy: false,
      batteryLevel: null,
    };
  },
  methods: {
    async refreshBattery() {
      return new Promise((resolve) => {
        uni.getBatteryInfo({
          success: (res) => {
            this.batteryLevel = Number(res.level);
            resolve();
          },
          fail: () => resolve(),
        });
      });
    },
    async sendHeartbeat() {
      try {
        await this.refreshBattery();
        await heartbeat("heartbeat", {
          battery_level: this.batteryLevel,
          app_active: true,
        });
      } catch (error) {
        console.log("heartbeat error:", error);
      }
    },
    async handleCheckin() {
      if (this.busy) return;
      this.busy = true;
      try {
        await this.refreshBattery();
        await heartbeat("checkin", {
          battery_level: this.batteryLevel,
          app_active: true,
        });
        this.statusText = "已通知家属：我很好";
        uni.showToast({ title: "已报平安", icon: "success" });
      } catch (error) {
        uni.showToast({ title: error.message || "报平安失败", icon: "none" });
      } finally {
        this.busy = false;
      }
    },
    startLongPress() {
      if (this.longPressTimer || this.busy) return;
      this.statusText = "长按中，保持 3 秒触发 SOS…";
      this.longPressTimer = setTimeout(async () => {
        this.longPressTimer = null;
        await this.handleSos();
      }, 3000);
    },
    cancelLongPress() {
      if (this.longPressTimer) {
        clearTimeout(this.longPressTimer);
        this.longPressTimer = null;
        this.statusText = "守护已开启";
      }
    },
    getLocation() {
      return new Promise((resolve) => {
        uni.getLocation({
          type: "gcj02",
          isHighAccuracy: true,
          success: (res) =>
            resolve({
              latitude: res.latitude,
              longitude: res.longitude,
              address: "",
            }),
          fail: () => resolve({}),
        });
      });
    },
    recordAudio10Seconds() {
      return new Promise((resolve, reject) => {
        const recorder = uni.getRecorderManager();
        const fs = uni.getFileSystemManager();
        let settled = false;

        recorder.onStop((res) => {
          if (settled) return;
          settled = true;
          fs.readFile({
            filePath: res.tempFilePath,
            encoding: "base64",
            success: (fileRes) => resolve(fileRes.data),
            fail: (error) => reject(error),
          });
        });
        recorder.onError((err) => {
          if (settled) return;
          settled = true;
          reject(err);
        });

        recorder.start({
          duration: 10000,
          sampleRate: 16000,
          numberOfChannels: 1,
          encodeBitRate: 96000,
          format: "wav",
        });
      });
    },
    async handleSos() {
      if (this.busy) return;
      this.busy = true;
      this.statusText = "SOS触发中：录音 10 秒 + 获取定位…";
      try {
        await this.refreshBattery();
        const [location, audioBase64] = await Promise.all([
          this.getLocation(),
          this.recordAudio10Seconds(),
        ]);
        await triggerSos({
          audio_base64: audioBase64,
          audio_format: "wav",
          location,
          battery_level: this.batteryLevel,
        });

        const familyPhone = uni.getStorageSync("family_phone");
        if (familyPhone) {
          uni.makePhoneCall({
            phoneNumber: familyPhone,
            fail: () => {},
          });
        }

        this.statusText = "SOS已发送，请保持电话畅通";
        uni.showToast({ title: "SOS 已发送", icon: "none", duration: 2500 });
      } catch (error) {
        this.statusText = "SOS发送失败，请重试";
        uni.showToast({ title: error.message || "SOS失败", icon: "none" });
      } finally {
        this.busy = false;
      }
    },
  },
  onLoad() {
    this.elderName = uni.getStorageSync("elder_name") || "爸爸";
    this.bindingCode = uni.getStorageSync("binding_code") || "------";
    this.sendHeartbeat();
    this.heartbeatTimer = setInterval(() => this.sendHeartbeat(), 5 * 60 * 1000);
  },
  onUnload() {
    if (this.longPressTimer) clearTimeout(this.longPressTimer);
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
  },
};
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 36rpx;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: center;
}

.head {
  margin-bottom: 30rpx;
}

.title {
  display: block;
  font-size: 50rpx;
  font-weight: 700;
}

.desc {
  display: block;
  margin-top: 12rpx;
  color: #666f7d;
  font-size: 30rpx;
}

.bind-code {
  display: block;
  margin-top: 12rpx;
  color: #1d4f91;
  font-size: 32rpx;
  font-weight: 600;
}

.safe-btn {
  width: 100%;
  height: 220rpx;
  line-height: 220rpx;
  border-radius: 24rpx;
  background: #12ab51;
  color: #ffffff;
  font-size: 60rpx;
  font-weight: 800;
}

.status {
  margin-top: 24rpx;
  text-align: center;
  color: #4f5765;
  font-size: 32rpx;
}
</style>

