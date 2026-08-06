const api = require('../../utils/api')

const KINDS = [
  { key: 'full', label: '完整报告' },
  { key: 'career', label: '事业专项' },
  { key: 'wealth', label: '财运专项' },
  { key: 'love', label: '婚恋专项' }
]

Page({
  data: { loading: true, exporting: false, hasChart: false, kind: 'full', kinds: KINDS, document: null, textPreview: '' },

  onShow() { this.loadReport() },

  async loadReport() {
    this.setData({ loading: true, textPreview: '' })
    try {
      const status = await api.request('/v1/session')
      if (!status.has_chart) {
        this.setData({ hasChart: false, document: null })
        return
      }
      const path = this.data.kind === 'full' ? '/v1/report' : `/v1/feature/${this.data.kind}`
      const document = await api.request(path)
      this.setData({ hasChart: true, document })
    } catch (error) { api.showError(error) }
    finally { this.setData({ loading: false }) }
  },

  chooseKind(event) {
    this.setData({ kind: event.currentTarget.dataset.kind, document: null })
    this.loadReport()
  },

  createChart() { wx.navigateTo({ url: '/pages/profile/index' }) },

  async exportText(event) {
    const format = event.currentTarget.dataset.format
    this.setData({ exporting: true })
    try {
      const text = await api.request(`/v1/export/${format}?kind=${this.data.kind}`, { timeout: 180000 })
      this.setData({ textPreview: String(text || '') })
      wx.setClipboardData({ data: String(text || ''), success: () => wx.showToast({ title: '已复制到剪贴板', icon: 'success' }) })
    } catch (error) { api.showError(error) }
    finally { this.setData({ exporting: false }) }
  },

  async exportPdf() {
    this.setData({ exporting: true })
    try {
      const path = await api.download(`/v1/export/pdf?kind=${this.data.kind}`)
      await new Promise((resolve, reject) => wx.openDocument({ filePath: path, fileType: 'pdf', showMenu: true, success: resolve, fail: reject }))
    } catch (error) { api.showError(error) }
    finally { this.setData({ exporting: false }) }
  }
})
