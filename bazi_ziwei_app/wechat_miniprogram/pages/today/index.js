const api = require('../../utils/api')

Page({
  data: { loading: true, error: '', daily: null, yearly: null },

  onShow() {
    this.loadGuidance()
  },

  async loadGuidance() {
    this.setData({ loading: true, error: '' })
    try {
      const result = await api.request('/v1/home')
      const daily = result.daily
      const yearly = result.yearly
      daily.colorText = (daily.lucky_colors || []).join('、')
      daily.actionText = (daily.suitable_actions || []).join('、')
      daily.avoidText = (daily.actions_to_avoid || []).join('、')
      yearly.keywordText = (yearly.keywords || []).join('、')
      yearly.actionText = (yearly.action_advice || []).join('、')
      this.setData({ daily, yearly })
    } catch (error) {
      this.setData({ error: error.message })
    } finally {
      this.setData({ loading: false })
    }
  },

  openPersonalYear() {
    wx.navigateTo({ url: `/pages/feature/index?type=yearly&year=${new Date().getFullYear()}` })
  },

  createChart() {
    wx.navigateTo({ url: '/pages/profile/index' })
  }
})
