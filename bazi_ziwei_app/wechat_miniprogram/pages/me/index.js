const api = require('../../utils/api')

Page({
  data: { loading: true, status: null, baseUrl: '', exporting: false, importing: false },

  onShow() { this.loadStatus() },

  async loadStatus() {
    this.setData({ loading: true, baseUrl: api.getBaseUrl() })
    try {
      const status = await api.request('/v1/session')
      this.setData({ status })
    } catch (error) { api.showError(error) }
    finally { this.setData({ loading: false }) }
  },

  openProfile() { wx.navigateTo({ url: '/pages/profile/index' }) },
  openArchives() { wx.navigateTo({ url: '/pages/archive/index' }) },
  openCompatibility() { wx.navigateTo({ url: '/pages/compatibility/index' }) },
  openSettings() { wx.navigateTo({ url: '/pages/settings/index' }) },
  openPrivacy() { wx.navigateTo({ url: '/pages/privacy/index' }) },
  openAcceptance() { wx.navigateTo({ url: '/pages/feature/index?type=acceptance' }) },

  async saveCurrent() {
    try {
      const result = await api.request('/v1/archives/current', { method: 'POST' })
      wx.showToast({ title: `档案 #${result.profile_id} 已保存`, icon: 'success' })
    } catch (error) { api.showError(error) }
  },

  async exportBackup() {
    this.setData({ exporting: true })
    try {
      const content = String(await api.request('/v1/backup'))
      const filePath = `${wx.env.USER_DATA_PATH}/命数研究室档案备份.json`
      await new Promise((resolve, reject) => wx.getFileSystemManager().writeFile({ filePath, data: content, encoding: 'utf8', success: resolve, fail: reject }))
      if (wx.shareFileMessage) {
        wx.shareFileMessage({ filePath, fileName: '命数研究室档案备份.json', fail: () => wx.setClipboardData({ data: content }) })
      } else {
        wx.setClipboardData({ data: content })
      }
    } catch (error) { api.showError(error) }
    finally { this.setData({ exporting: false }) }
  },

  importBackup() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['json'],
      success: async result => {
        this.setData({ importing: true })
        try {
          const content = await new Promise((resolve, reject) => wx.getFileSystemManager().readFile({ filePath: result.tempFiles[0].path, encoding: 'utf8', success: res => resolve(res.data), fail: reject }))
          const imported = await api.request('/v1/backup/import', { method: 'POST', data: { payload: content }, timeout: 180000 })
          wx.showModal({ title: '恢复完成', content: `已导入 ${imported.imported || 0} 条，拒绝 ${imported.rejected || 0} 条`, showCancel: false })
        } catch (error) { api.showError(error) }
        finally { this.setData({ importing: false }) }
      }
    })
  },

  async exportDatabase() {
    this.setData({ exporting: true })
    try {
      const filePath = await api.download('/v1/backup/database')
      if (wx.shareFileMessage) {
        wx.shareFileMessage({ filePath, fileName: '命数研究室_SQLite备份.db' })
      } else {
        wx.showModal({ title: '备份已生成', content: '当前微信基础库不支持直接转发文件，请在开发者工具 Network 面板下载该响应。', showCancel: false })
      }
    } catch (error) { api.showError(error) }
    finally { this.setData({ exporting: false }) }
  },

  clearCurrent() {
    wx.showModal({
      title: '清除当前会话？',
      content: '只清除当前命盘和问答记录，不会删除已保存档案。',
      confirmColor: '#B91C1C',
      success: async result => {
        if (!result.confirm) return
        try {
          await api.request('/v1/session', { method: 'DELETE' })
          wx.showToast({ title: '已清除', icon: 'success' })
          this.loadStatus()
        } catch (error) { api.showError(error) }
      }
    })
  }
})
