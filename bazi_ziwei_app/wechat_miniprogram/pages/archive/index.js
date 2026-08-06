const api = require('../../utils/api')

Page({
  data: { loading: true, keyword: '', gender: '全部', genders: ['全部', '男', '女'], genderIndex: 0, items: [] },

  onShow() { this.loadArchives() },
  updateKeyword(event) { this.setData({ keyword: event.detail.value }) },
  changeGender(event) {
    const genderIndex = Number(event.detail.value)
    this.setData({ genderIndex, gender: this.data.genders[genderIndex] })
    this.loadArchives()
  },

  async loadArchives() {
    this.setData({ loading: true })
    try {
      const result = await api.request(`/v1/archives?keyword=${encodeURIComponent(this.data.keyword)}&gender=${encodeURIComponent(this.data.gender)}`)
      const items = (result.items || []).map(item => ({ ...item, calendarLabel: item.calendar_type === 'lunar' ? '农历' : '公历' }))
      this.setData({ items })
    } catch (error) { api.showError(error) }
    finally { this.setData({ loading: false }) }
  },

  createChart() { wx.navigateTo({ url: '/pages/profile/index' }) },
  findItem(id) { return this.data.items.find(item => item.id === Number(id)) },

  async loadItem(event) {
    try {
      await api.request(`/v1/archives/${event.currentTarget.dataset.id}/load`, { method: 'POST', timeout: 120000 })
      wx.showToast({ title: '命盘已载入', icon: 'success' })
      setTimeout(() => wx.switchTab({ url: '/pages/chart/index' }), 350)
    } catch (error) { api.showError(error) }
  },

  editItem(event) {
    const item = this.findItem(event.currentTarget.dataset.id)
    if (!item) return
    wx.setStorageSync('mingshu_edit_profile', item)
    wx.navigateTo({ url: '/pages/profile/index?edit=1' })
  },

  deleteItem(event) {
    const item = this.findItem(event.currentTarget.dataset.id)
    if (!item) return
    wx.showModal({
      title: `删除“${item.name || '未命名'}”？`,
      content: '这会删除本机档案及其保存的报告，操作不可撤销。',
      confirmColor: '#B91C1C',
      success: async result => {
        if (!result.confirm) return
        try {
          await api.request(`/v1/archives/${item.id}`, { method: 'DELETE' })
          wx.showToast({ title: '已删除', icon: 'success' })
          this.loadArchives()
        } catch (error) { api.showError(error) }
      }
    })
  }
})
