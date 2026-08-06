const api = require('../../utils/api')

const LENGTHS = ['简洁版', '标准版', '详细版']
const FORMATS = ['Markdown', 'TXT', 'PDF']

Page({
  data: {
    baseUrl: '',
    lengths: LENGTHS,
    formats: FORMATS,
    lengthIndex: 1,
    formatIndex: 0,
    form: { report_length: '标准版', show_technical_details: false, show_disclaimer: true, default_export_format: 'Markdown', enable_quality_check: true },
    loading: true,
    saving: false,
    connectionText: ''
  },

  onLoad() { this.loadSettings() },

  async loadSettings() {
    this.setData({ loading: true, baseUrl: api.getBaseUrl() })
    try {
      const form = await api.request('/v1/settings')
      this.setData({ form, lengthIndex: Math.max(0, LENGTHS.indexOf(form.report_length)), formatIndex: Math.max(0, FORMATS.indexOf(form.default_export_format)) })
    } catch (error) { api.showError(error) }
    finally { this.setData({ loading: false }) }
  },

  updateBaseUrl(event) { this.setData({ baseUrl: event.detail.value, connectionText: '' }) },
  changeLength(event) {
    const lengthIndex = Number(event.detail.value)
    this.setData({ lengthIndex, 'form.report_length': LENGTHS[lengthIndex] })
  },
  changeFormat(event) {
    const formatIndex = Number(event.detail.value)
    this.setData({ formatIndex, 'form.default_export_format': FORMATS[formatIndex] })
  },
  updateSwitch(event) { this.setData({ [`form.${event.currentTarget.dataset.field}`]: event.detail.value }) },

  async testConnection() {
    api.setBaseUrl(this.data.baseUrl)
    this.setData({ baseUrl: api.getBaseUrl(), connectionText: '连接中…' })
    try {
      const result = await api.request('/health')
      this.setData({ connectionText: result.ok ? '连接成功 · 本地测试服务正常' : '服务返回异常' })
    } catch (error) { this.setData({ connectionText: error.message }) }
  },

  async saveSettings() {
    this.setData({ saving: true })
    try {
      api.setBaseUrl(this.data.baseUrl)
      await api.request('/v1/settings', { method: 'PUT', data: this.data.form })
      this.setData({ baseUrl: api.getBaseUrl() })
      wx.showToast({ title: '设置已保存', icon: 'success' })
    } catch (error) { api.showError(error) }
    finally { this.setData({ saving: false }) }
  }
})
