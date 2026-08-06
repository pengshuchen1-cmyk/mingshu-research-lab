const api = require('../../utils/api')

const hours = Array.from({ length: 24 }, (_, index) => `${String(index).padStart(2, '0')} 时`)
const minutes = Array.from({ length: 60 }, (_, index) => `${String(index).padStart(2, '0')} 分`)

Page({
  data: {
    form: {
      name: '', gender: '男', calendar_type: 'solar', birth_date: '1990-01-01',
      birth_hour: 10, birth_minute: 0, birth_place: '', is_leap_month: false,
      time_known: true, note: ''
    },
    hours,
    minutes,
    preview: null,
    privacyConsent: false,
    saveArchive: false,
    loading: false,
    profileId: null,
    editing: false
  },

  onLoad(options) {
    const editing = wx.getStorageSync('mingshu_edit_profile')
    if (options.edit === '1' && editing) {
      const form = {
        name: editing.name || '',
        gender: editing.gender || '男',
        calendar_type: editing.calendar_type || 'solar',
        birth_date: editing.calendar_type === 'lunar' ? (editing.lunar_birth_date || editing.birth_date) : editing.birth_date,
        birth_hour: editing.birth_hour === null ? 10 : Number(editing.birth_hour || 0),
        birth_minute: editing.birth_minute === null ? 0 : Number(editing.birth_minute || 0),
        birth_place: editing.birth_place || '',
        is_leap_month: Boolean(editing.is_leap_month),
        time_known: editing.birth_hour !== null,
        note: editing.note || ''
      }
      this.setData({ form, profileId: editing.id, editing: true, privacyConsent: true })
      wx.setNavigationBarTitle({ title: '编辑并重新排盘' })
    }
  },

  updateField(event) {
    const field = event.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: event.detail.value, preview: null })
  },

  updateGender(event) {
    this.setData({ 'form.gender': event.detail.value, preview: null })
  },

  updateCalendar(event) {
    this.setData({ 'form.calendar_type': event.detail.value, 'form.is_leap_month': false, preview: null })
  },

  updateDate(event) {
    this.setData({ 'form.birth_date': event.detail.value, preview: null })
  },

  updateHour(event) {
    this.setData({ 'form.birth_hour': Number(event.detail.value), preview: null })
  },

  updateMinute(event) {
    this.setData({ 'form.birth_minute': Number(event.detail.value), preview: null })
  },

  updateTimeKnown(event) {
    this.setData({ 'form.time_known': event.detail.value, preview: null })
  },

  updateLeap(event) {
    this.setData({ 'form.is_leap_month': event.detail.value, preview: null })
  },

  updateConsent(event) {
    this.setData({ privacyConsent: event.detail.value })
  },

  updateSave(event) {
    this.setData({ saveArchive: event.detail.value })
  },

  async previewChart() {
    if (!this.data.privacyConsent) {
      wx.showToast({ title: '请先同意本次测试隐私说明', icon: 'none' })
      return
    }
    this.setData({ loading: true })
    try {
      const preview = await api.request('/v1/profile/preview', { method: 'POST', data: this.data.form })
      preview.pillarText = (preview.pillars || []).join(' / ')
      this.setData({ preview })
    } catch (error) {
      api.showError(error)
    } finally {
      this.setData({ loading: false })
    }
  },

  async generateChart() {
    if (!this.data.preview) {
      wx.showToast({ title: '请先校验并预览', icon: 'none' })
      return
    }
    this.setData({ loading: true })
    try {
      if (this.data.editing) {
        await api.request(`/v1/archives/${this.data.profileId}/chart`, { method: 'PUT', data: this.data.form, timeout: 120000 })
        wx.removeStorageSync('mingshu_edit_profile')
      } else {
        await api.request(`/v1/profile/chart?save=${this.data.saveArchive ? 'true' : 'false'}`, { method: 'POST', data: this.data.form, timeout: 120000 })
      }
      wx.showToast({ title: '命盘已生成', icon: 'success' })
      setTimeout(() => wx.switchTab({ url: '/pages/chart/index' }), 450)
    } catch (error) {
      api.showError(error)
    } finally {
      this.setData({ loading: false })
    }
  }
})
