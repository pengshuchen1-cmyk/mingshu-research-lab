const api = require('../../utils/api')

Page({
  clearSession() {
    wx.showModal({
      title: '立即清除本次会话？',
      content: '将清除当前出生资料、命盘、报告与 AI 问答记录，不影响已保存的本机档案。',
      confirmColor: '#B91C1C',
      success: async result => {
        if (!result.confirm) return
        try {
          await api.request('/v1/session', { method: 'DELETE' })
          wx.showToast({ title: '会话已清除', icon: 'success' })
          setTimeout(() => wx.switchTab({ url: '/pages/home/index' }), 350)
        } catch (error) { api.showError(error) }
      }
    })
  }
})
