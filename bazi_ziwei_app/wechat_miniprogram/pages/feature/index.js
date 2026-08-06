const api = require('../../utils/api')

const TITLES = {
  bazi: '八字排盘', overview: '命盘总览', 'five-elements': '五行喜忌',
  'sixty-jiazi': '六十甲子', luck: '大运流年', yearly: '年度运程',
  career: '事业专项', wealth: '财运专项', love: '婚恋专项',
  ziwei: '紫微斗数', acceptance: '验收中心'
}

Page({
  data: {
    type: 'overview',
    title: '命盘总览',
    year: new Date().getFullYear(),
    yearRange: [],
    yearIndex: 10,
    document: null,
    loading: true,
    error: '',
    needsChart: false
  },

  onLoad(options) {
    const current = new Date().getFullYear()
    const yearRange = Array.from({ length: 21 }, (_, index) => current - 10 + index)
    const year = Number(options.year || current)
    const type = options.type || 'overview'
    this.setData({ type, title: TITLES[type] || '命理分析', year, yearRange, yearIndex: Math.max(0, yearRange.indexOf(year)) })
    wx.setNavigationBarTitle({ title: TITLES[type] || '命数研究室' })
    this.loadDocument()
  },

  async loadDocument() {
    this.setData({ loading: true, error: '', needsChart: false })
    try {
      const document = await api.request(`/v1/feature/${this.data.type}?year=${this.data.year}`)
      this.setData({ document })
    } catch (error) {
      const needsChart = error.message.indexOf('命盘') >= 0
      this.setData({ error: error.message, needsChart })
    } finally {
      this.setData({ loading: false })
    }
  },

  changeYear(event) {
    const yearIndex = Number(event.detail.value)
    this.setData({ yearIndex, year: this.data.yearRange[yearIndex], document: null })
    this.loadDocument()
  },

  createChart() {
    wx.navigateTo({ url: '/pages/profile/index' })
  }
})
