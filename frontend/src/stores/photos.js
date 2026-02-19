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
    scanStatus: {
      status: 'idle',
      total_photos: 0,
      new_photos: 0,
      pending: 0,
      duplicate_photos: 0,
      analyzing: 0,
      analyzed: 0
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
      const poll = async () => {
        try {
          const response = await scannerApi.getStatus()
          this.scanStatus = response.data
          
          // 如果还在运行，继续轮询
          if (response.data.status === 'running') {
            setTimeout(poll, 2000)
            // 同时刷新照片列表
            this.fetchPhotos()
          }
        } catch (error) {
          console.error('获取扫描状态失败:', error)
        }
      }
      poll()
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
