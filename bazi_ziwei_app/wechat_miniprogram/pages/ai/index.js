const api = require('../../utils/api')

const SUGGESTIONS = ['我的事业优势和近期重点是什么？', '今年财务上需要注意什么？', '我的关系模式有哪些沟通建议？', '请用通俗语言总结我的命盘。']

Page({
  data: {
    loading: true,
    asking: false,
    hasChart: false,
    messages: [],
    question: '',
    suggestions: SUGGESTIONS,
    scrollTarget: ''
  },

  onShow() { this.initialize() },

  async initialize() {
    this.setData({ loading: true })
    try {
      const status = await api.request('/v1/session')
      let messages = []
      if (status.has_chart) {
        const history = await api.request('/v1/ai/history')
        messages = (history.items || []).map(item => ({ role: item.role, content: item.content }))
      }
      this.setData({ hasChart: status.has_chart, messages })
      this.scrollToBottom(messages)
    } catch (error) { api.showError(error) }
    finally { this.setData({ loading: false }) }
  },

  updateQuestion(event) { this.setData({ question: event.detail.value }) },
  chooseSuggestion(event) { this.setData({ question: event.currentTarget.dataset.text }) },
  createChart() { wx.navigateTo({ url: '/pages/profile/index' }) },

  scrollToBottom(messages) {
    if (messages.length) this.setData({ scrollTarget: `message-${messages.length - 1}` })
  },

  async sendQuestion() {
    const question = this.data.question.trim()
    if (!question || this.data.asking) return
    const messages = [...this.data.messages, { role: 'user', content: question }]
    this.setData({ messages, question: '', asking: true })
    this.scrollToBottom(messages)
    try {
      const result = await api.request('/v1/ai/ask', { method: 'POST', data: { question }, timeout: 180000 })
      messages.push({
        role: 'assistant',
        content: result.answer,
        source: result.source || '',
        degraded: result.degraded_reason || '',
        advice: Array.isArray(result.practical_advice) ? result.practical_advice.join('；') : (result.practical_advice || '')
      })
      this.setData({ messages })
    } catch (error) {
      messages.push({ role: 'assistant', content: `本次回答失败：${error.message}`, error: true })
      this.setData({ messages })
    } finally {
      this.setData({ asking: false })
      this.scrollToBottom(messages)
    }
  }
})
