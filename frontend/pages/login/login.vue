<template>
  <view class="page">
    <text class="title">我很好</text>
    <text class="subtitle">老人本人手机号登录</text>

    <input
      class="input"
      type="number"
      maxlength="11"
      v-model="phone"
      placeholder="请输入手机号"
    />

    <view class="row">
      <input
        class="input code-input"
        type="number"
        maxlength="6"
        v-model="code"
        placeholder="请输入验证码"
      />
      <button class="mini-btn" :disabled="sending" @click="handleSendCode(false)">
        获取验证码
      </button>
    </view>

    <button class="voice-btn" :disabled="sending" @click="handleSendCode(true)">
      🔊 语音读验证码
    </button>

    <button class="login-btn" :disabled="loading" @click="handleLogin">进入守护主页</button>

    <text class="tips">{{ tips }}</text>
  </view>
</template>

<script>
import { elderLogin, sendCode } from "../../utils/api";

export default {
  data() {
    return {
      phone: "",
      code: "",
      tips: "无需注册、无需密码",
      sending: false,
      loading: false,
      audioCtx: null,
    };
  },
  methods: {
    validPhone(value) {
      return /^1[3-9]\d{9}$/.test(value);
    },
    async handleSendCode(readAloud) {
      if (!this.validPhone(this.phone)) {
        uni.showToast({ title: "请输入正确手机号", icon: "none" });
        return;
      }
      this.sending = true;
      try {
        const data = await sendCode(this.phone, readAloud);
        this.tips = data.debug_code
          ? `测试验证码：${data.debug_code}（仅测试模式）`
          : "验证码已发送（5分钟有效）";
        if (readAloud && data.voice_audio_base64) {
          this.playAudio(data.voice_audio_base64);
        } else if (readAloud) {
          uni.showToast({ title: "语音暂不可用，请看短信", icon: "none" });
        }
      } catch (error) {
        uni.showToast({ title: error.message || "发送失败", icon: "none" });
      } finally {
        this.sending = false;
      }
    },
    playAudio(base64Text) {
      if (this.audioCtx) {
        this.audioCtx.destroy();
      }
      const ctx = uni.createInnerAudioContext();
      ctx.src = `data:audio/wav;base64,${base64Text}`;
      ctx.play();
      this.audioCtx = ctx;
    },
    async handleLogin() {
      if (!this.validPhone(this.phone)) {
        uni.showToast({ title: "请输入正确手机号", icon: "none" });
        return;
      }
      if (!/^\d{6}$/.test(this.code)) {
        uni.showToast({ title: "请输入6位验证码", icon: "none" });
        return;
      }
      this.loading = true;
      try {
        const data = await elderLogin(this.phone, this.code);
        uni.setStorageSync("good_token", data.token);
        uni.setStorageSync("binding_code", data.binding_code);
        uni.setStorageSync("elder_name", data.user.name || "爸爸");
        uni.showToast({ title: "登录成功", icon: "success" });
        uni.reLaunch({ url: "/pages/index/index" });
      } catch (error) {
        uni.showToast({ title: error.message || "登录失败", icon: "none" });
      } finally {
        this.loading = false;
      }
    },
  },
  onUnload() {
    if (this.audioCtx) {
      this.audioCtx.destroy();
    }
  },
};
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 36rpx;
  background: #f7f8fa;
}

.title {
  display: block;
  font-size: 60rpx;
  font-weight: 700;
  margin-top: 60rpx;
}

.subtitle {
  display: block;
  color: #6a7280;
  font-size: 32rpx;
  margin: 16rpx 0 48rpx;
}

.input {
  width: 100%;
  height: 96rpx;
  border: 2rpx solid #d6dae1;
  border-radius: 16rpx;
  background: #fff;
  padding: 0 24rpx;
  font-size: 34rpx;
  box-sizing: border-box;
  margin-bottom: 20rpx;
}

.row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.code-input {
  flex: 1;
}

.mini-btn {
  min-width: 220rpx;
  height: 96rpx;
  line-height: 96rpx;
  border-radius: 16rpx;
  font-size: 30rpx;
  color: #ffffff;
  background: #1f6feb;
}

.voice-btn {
  width: 100%;
  height: 98rpx;
  line-height: 98rpx;
  border-radius: 16rpx;
  font-size: 32rpx;
  background: #fff;
  border: 2rpx solid #2a8f55;
  color: #2a8f55;
  margin: 12rpx 0 24rpx;
}

.login-btn {
  width: 100%;
  height: 108rpx;
  line-height: 108rpx;
  border-radius: 18rpx;
  background: #19a354;
  color: #ffffff;
  font-size: 38rpx;
  font-weight: 700;
}

.tips {
  display: block;
  font-size: 30rpx;
  color: #616a79;
  margin-top: 22rpx;
}
</style>

