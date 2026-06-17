import { defineStore } from 'pinia'
import { photoApi, scannerApi, analyzeApi } from '@/api'

export const usePhotoStore = defineStore('photos', {
  state: () => ({
    photos: [],
    total: 0,
    loading: false,
    currentPage: 1,
    pageSize: 20,
    sortBy: 'taken_at',
    sortOrder: 'desc',
    filterStatus: '',
    filterYear: null,
    filterMonth: null,
    filterMemoryScoreMin: null,
    filterMemoryScoreMax: null,
    filterAestheticScoreMin: null,
    filterAestheticScoreMax: null,
    filterHasCaption: null,
    stats: null,
    scanStatus: {
      status: 'idle',
      scanner_status: 'idle',
      analyzer_status: 'idle',
      total_photos: 0,
      new_photos: 0,
      pending: 0,
      duplicate_photos: 0,
      analyzing: 0,
      analyzed: 0,
      avg_analyze_time: null,
      estimated_remaining_seconds: null,
      current_photo_id: null,
      current_photo_filename: null
    }
  }),

  getters: {
    pendingPhotos: (state) => state.photos.filter(p => p.status === 'pending'),
    analyzedPhotos: (state) => state.photos.filter(p => p.status === 'analyzed'),
    duplicatePhotos: (state) => state.photos.filter(p => p.status === 'duplicate'),
    highMemoryPhotos: (state) => state.photos
      .filter(p => p.memory_score !== null)
      .sort((a, b) => b.memory_score - a.memory_score)
  },

  actions: {
    async fetchPhotos(params = {}) {
      this.loading = true
      console.log('[Gallery] 开始加载照片...')
      try {
        const response = await photoApi.getPhotos({
          page: this.currentPage,
          page_size: this.pageSize,
          sort_by: this.sortBy,
          sort_order: this.sortOrder,
          status: this.filterStatus || undefined,
          year: this.filterYear || undefined,
          month: this.filterMonth || undefined,
          memory_score_min: this.filterMemoryScoreMin || undefined,
          memory_score_max: this.filterMemoryScoreMax || undefined,
          aesthetic_score_min: this.filterAestheticScoreMin || undefined,
          aesthetic_score_max: this.filterAestheticScoreMax || undefined,
          has_caption: this.filterHasCaption || undefined,
          ...params
        })
        console.log('[Gallery] API 响应:', response.data)
        this.photos = response.data.photos
        this.total = response.data.total
        console.log(`[Gallery] 加载完成: ${this.photos.length} 张照片, 共 ${this.total} 张`)
      } catch (error) {
        console.error('[Gallery] 获取照片失败:', error)
        alert('加载照片失败: ' + (error.response?.data?.detail || error.message))
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchStats() {
      try {
        const response = await photoApi.getStats()
        this.stats = response.data
        console.log('[Gallery] 统计信息:', this.stats)
      } catch (error) {
        console.error('[Gallery] 获取统计失败:', error)
      }
    },

    setYearFilter(year) {
      this.filterYear = year
      this.filterMonth = null
      this.currentPage = 1
      this.fetchPhotos()
    },

    setMonthFilter(month) {
      this.filterMonth = month
      this.currentPage = 1
      this.fetchPhotos()
    },

    setScoreFilter(type, min, max) {
      if (type === 'memory') {
        this.filterMemoryScoreMin = min
        this.filterMemoryScoreMax = max
      } else if (type === 'aesthetic') {
        this.filterAestheticScoreMin = min
        this.filterAestheticScoreMax = max
      }
      this.currentPage = 1
      this.fetchPhotos()
    },

    setHasCaptionFilter(hasCaption) {
      this.filterHasCaption = hasCaption
      this.currentPage = 1
      this.fetchPhotos()
    },

    clearFilters() {
      this.filterYear = null
      this.filterMonth = null
      this.filterMemoryScoreMin = null
      this.filterMemoryScoreMax = null
      this.filterAestheticScoreMin = null
      this.filterAestheticScoreMax = null
      this.filterHasCaption = null
      this.currentPage = 1
      this.fetchPhotos()
    },

    setSort(sortBy, sortOrder = 'desc') {
      this.sortBy = sortBy
      this.sortOrder = sortOrder
      this.fetchPhotos()
    },

    setFilter(status) {
      this.filterStatus = status
      this.currentPage = 1
      this.fetchPhotos()
    },

    async startScan(path = null) {
      try {
        await scannerApi.startScan({ path, recursive: true })
        // 开始轮询状态
        this.pollScanStatus()
      } catch (error) {
        console.error('启动扫描失败:', error)
        throw error
      }
    },

    async pollScanStatus() {
      try {
        const response = await scannerApi.getStatus()
        this.scanStatus = response.data
        
        // 如果还在运行，继续轮询
        if (response.data.status === 'running') {
          setTimeout(() => this.pollScanStatus(), 2000)
        }
      } catch (error) {
        console.error('获取扫描状态失败:', error)
      }
    },

    async batchAnalyze(photoIds, force = false) {
      try {
        const response = await analyzeApi.batchAnalyze(photoIds, force)
        return response.data
      } catch (error) {
        console.error('批量分析失败:', error)
        throw error
      }
    },
    
    async analyzeAll() {
      try {
        const response = await analyzeApi.analyzeAll()
        return response.data
      } catch (error) {
        console.error('分析失败:', error)
        throw error
      }
    },

    async reanalyzePhoto(photoId) {
      try {
        await analyzeApi.reanalyze(photoId)
        // 刷新照片列表
        await this.fetchPhotos()
      } catch (error) {
        console.error('重新分析失败:', error)
        throw error
      }
    },

    setPage(page) {
      this.currentPage = page
      this.fetchPhotos()
    }
  }
})
