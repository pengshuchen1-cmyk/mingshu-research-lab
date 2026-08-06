const api = require('./utils/api')

App({
  globalData: {
    apiBaseUrl: api.getBaseUrl(),
    sessionId: api.getSessionId()
  },

  onLaunch() {
    api.getSessionId()
  }
})
