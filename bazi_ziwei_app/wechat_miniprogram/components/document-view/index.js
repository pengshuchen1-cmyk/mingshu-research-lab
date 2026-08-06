Component({
  properties: {
    document: { type: Object, value: null }
  },

  data: {
    activeMonthItem: -1,
    activeMonthSection: -1
  },

  methods: {
    toggleCard(event) {
      const sectionIndex = Number(event.currentTarget.dataset.section)
      const itemIndex = Number(event.currentTarget.dataset.item)
      const kind = event.currentTarget.dataset.kind
      if (kind !== 'months') return
      const isActive = this.data.activeMonthSection === sectionIndex && this.data.activeMonthItem === itemIndex
      this.setData({
        activeMonthSection: isActive ? -1 : sectionIndex,
        activeMonthItem: isActive ? -1 : itemIndex
      })
    }
  }
})
