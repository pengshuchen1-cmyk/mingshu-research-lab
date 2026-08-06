const api = require('../../utils/api')

Page({
  data: { loading: true, error: '', status: null, document: null, features: [] },

  onShow() {
    this.loadChart()
  },

  async loadChart() {
    this.setData({ loading: true, error: '' })
    try {
      const status = await api.request('/v1/session')
      if (!status.has_chart) {
        this.setData({ status, document: null, features: [] })
        return
      }
      const [document, featureResult] = await Promise.all([
        api.request('/v1/feature/overview'),
        api.request('/v1/features')
      ])
      this.setData({ status, document, features: (featureResult.items || []).filter(item => item.key !== 'compatibility') })
    } catch (error) {
      this.setData({ error: error.message })
    } finally {
      this.setData({ loading: false })
    }
  },

  createChart() { wx.navigateTo({ url: '/pages/profile/index' }) },
  openArchive() { wx.navigateTo({ url: '/pages/archive/index' }) },
  openFeature(event) { wx.navigateTo({ url: event.currentTarget.dataset.route }) },

  async saveCurrent() {
    try {
      const result = await api.request('/v1/archives/current', { method: 'POST' })
      wx.showToast({ title: `已保存 #${result.profile_id}`, icon: 'success' })
    } catch (error) { api.showError(error) }
  }
})
