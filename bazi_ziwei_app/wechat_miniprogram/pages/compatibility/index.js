const api = require('../../utils/api')

Page({
  data: { loading: true, analyzing: false, profiles: [], firstIndex: 0, secondIndex: 1, document: null },

  onShow() { this.loadProfiles() },

  async loadProfiles() {
    this.setData({ loading: true })
    try {
      const result = await api.request('/v1/archives')
      const profiles = (result.items || []).map(item => ({ ...item, displayName: `${item.name || '未命名'}｜${item.gender}｜${item.birth_date}` }))
      this.setData({ profiles, secondIndex: profiles.length > 1 ? 1 : 0 })
    } catch (error) { api.showError(error) }
    finally { this.setData({ loading: false }) }
  },

  chooseFirst(event) { this.setData({ firstIndex: Number(event.detail.value), document: null }) },
  chooseSecond(event) { this.setData({ secondIndex: Number(event.detail.value), document: null }) },
  createProfile() { wx.navigateTo({ url: '/pages/profile/index' }) },

  async analyze() {
    const first = this.data.profiles[this.data.firstIndex]
    const second = this.data.profiles[this.data.secondIndex]
    if (!first || !second || first.id === second.id) {
      wx.showToast({ title: '请选择两个不同的档案', icon: 'none' })
      return
    }
    this.setData({ analyzing: true, document: null })
    try {
      const document = await api.request('/v1/compatibility', { method: 'POST', data: { first_profile_id: first.id, second_profile_id: second.id }, timeout: 180000 })
      this.setData({ document })
    } catch (error) { api.showError(error) }
    finally { this.setData({ analyzing: false }) }
  }
})
