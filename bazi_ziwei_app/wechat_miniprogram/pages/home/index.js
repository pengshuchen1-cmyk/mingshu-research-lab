const api = require('../../utils/api')

Page({
  data: {
    loading: true,
    error: '',
    content: null
  },

  onLoad() {
    this.loadHome()
  },

  async loadHome() {
    this.setData({ loading: true, error: '' })
    try {
      const content = await api.request('/v1/home')
      content.daily.colorText = (content.daily.lucky_colors || []).join('、')
      content.daily.focusText = (content.daily.suitable_actions || [])[0] || '稳步推进'
      content.features = (content.features || []).map((item, index) => ({
        ...item,
        displayIndex: String(index + 1).padStart(2, '0')
      }))
      this.setData({ content })
    } catch (error) {
      this.setData({ error: error.message })
    } finally {
      this.setData({ loading: false })
    }
  },

  startChart() {
    wx.navigateTo({ url: '/pages/profile/index' })
  },

  openToday() {
    wx.switchTab({ url: '/pages/today/index' })
  },

  openChart() {
    wx.switchTab({ url: '/pages/chart/index' })
  },

  openReport() {
    wx.switchTab({ url: '/pages/report/index' })
  },

  openMe() {
    wx.switchTab({ url: '/pages/me/index' })
  },

  openFeature(event) {
    const route = event.currentTarget.dataset.route
    if (route) wx.navigateTo({ url: route })
  }
})
