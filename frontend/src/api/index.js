import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 照片相关 API
export const photoApi = {
  // 获取照片列表
  getPhotos: (params = {}) => api.get('/photos/', { params }),
  
  // 获取照片统计
  getStats: () => api.get('/photos/stats'),
  
  // 获取单张照片
  getPhoto: (id) => api.get(`/photos/${id}`),
  
  // 删除照片
  deletePhoto: (id) => api.delete(`/photos/${id}`)
}

// 扫描相关 API
export const scannerApi = {
  // 开始扫描
  startScan: (data = {}) => api.post('/scanner/start', data),
  
  // 获取扫描状态
  getStatus: () => api.get('/scanner/status')
}

// 分析相关 API
export const analyzeApi = {
  // 分析所有待处理照片
  analyzeAll: () => api.post('/analyze/all'),
  
  // 批量分析（保留用于重试特定照片）
  batchAnalyze: (photoIds, force = false) => 
    api.post('/analyze/batch', { photo_ids: photoIds, force_reanalyze: force }),
  
  // 获取分析结果
  getAnalysis: (photoId) => api.get(`/analyze/${photoId}`),
  
  // 重新分析
  reanalyze: (photoId) => api.post(`/analyze/${photoId}/reanalyze`)
}

// 导出相关 API
export const exportApi = {
  // 生成预览
  preview: (data) => api.post('/export/preview', data, { responseType: 'blob' }),
  
  // 导出单张
  exportSingle: (data) => api.post('/export/single', data),
  
  // 批量导出
  batchExport: (data) => api.post('/export/batch', data),
  
  // 获取导出历史
  getHistory: (params = {}) => api.get('/export/history', { params })
}

export default api
