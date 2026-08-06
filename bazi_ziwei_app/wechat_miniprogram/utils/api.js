const DEFAULT_BASE_URL = 'http://127.0.0.1:8502/api'

function getBaseUrl() {
  return wx.getStorageSync('mingshu_api_base_url') || DEFAULT_BASE_URL
}

function setBaseUrl(value) {
  const normalized = String(value || '').replace(/\/+$/, '')
  wx.setStorageSync('mingshu_api_base_url', normalized || DEFAULT_BASE_URL)
  return normalized || DEFAULT_BASE_URL
}

function getSessionId() {
  let value = wx.getStorageSync('mingshu_session_id')
  if (!value) {
    value = `mini-${Date.now()}-${Math.random().toString(16).slice(2)}`
    wx.setStorageSync('mingshu_session_id', value)
  }
  return value
}

function request(path, options = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${getBaseUrl()}${path}`,
      method: options.method || 'GET',
      data: options.data,
      timeout: options.timeout || 120000,
      header: {
        'content-type': 'application/json',
        'X-Session-Id': getSessionId(),
        ...(options.header || {})
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
          return
        }
        const message = (res.data && (res.data.detail || res.data.message)) || `请求失败（${res.statusCode}）`
        reject(new Error(typeof message === 'string' ? message : JSON.stringify(message)))
      },
      fail(error) {
        reject(new Error(error.errMsg || '无法连接本地 API，请确认 8502 端口已启动。'))
      }
    })
  })
}

function download(path) {
  return new Promise((resolve, reject) => {
    wx.downloadFile({
      url: `${getBaseUrl()}${path}`,
      header: { 'X-Session-Id': getSessionId() },
      timeout: 120000,
      success(res) {
        if (res.statusCode === 200) resolve(res.tempFilePath)
        else reject(new Error(`下载失败（${res.statusCode}）`))
      },
      fail(error) {
        reject(new Error(error.errMsg || '下载失败'))
      }
    })
  })
}

function showError(error) {
  wx.showToast({ title: error.message || '操作失败', icon: 'none', duration: 3000 })
}

module.exports = {
  getBaseUrl,
  setBaseUrl,
  getSessionId,
  request,
  download,
  showError
}
