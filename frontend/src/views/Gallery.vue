<template>
  <div class="gallery">
    <header class="gallery-header">
      <button class="back-btn" @click="$router.push('/')">←</button>
      <h1>照片库</h1>
        <div class="filter-bar">
          <select v-model="photoStore.filterStatus" @change="applyFilter">
            <option value="">全部</option>
            <option value="analyzed">已分析</option>
            <option value="pending">待处理</option>
            <option value="error">分析失败</option>
            <option value="duplicate">重复</option>
          </select>
          <select v-model="photoStore.sortBy" @change="onSortChange">
            <option value="taken_at">按时间</option>
            <option value="memory_score">按回忆分</option>
            <option value="aesthetic_score">按美观分</option>
          </select>
          <span class="sort-indicator" v-if="photoStore.sortBy !== 'taken_at'">
            {{ sortLabels[photoStore.sortBy] }}
          </span>
          <button 
            v-if="photoStore.filterStatus === 'error' && photoStore.photos.length > 0" 
            class="reset-error-btn"
            @click="resetErrorPhotos"
          >
            重置 {{ photoStore.photos.length }} 张失败照片
          </button>
          <button class="toggle-sidebar-btn" @click="showSidebar = !showSidebar">
            {{ showSidebar ? '隐藏筛选' : '显示筛选' }}
          </button>
        </div>
    </header>
    
    <div class="gallery-body">
      <!-- 侧边栏 -->
      <aside class="sidebar" v-if="showSidebar">
        <div class="sidebar-section">
          <h3>快速筛选</h3>
          <button 
            class="quick-filter-btn"
            :class="{ active: !photoStore.filterYear && !photoStore.filterMemoryScoreMin }"
            @click="photoStore.clearFilters()"
          >
            全部照片 ({{ photoStore.stats?.total || 0 }})
          </button>
        </div>
        
        <div class="sidebar-section" v-if="photoStore.stats?.years?.length">
          <h3>按年份</h3>
          <div class="year-list">
            <button 
              v-for="yearStat in photoStore.stats.years" 
              :key="yearStat.year"
              class="year-btn"
              :class="{ active: photoStore.filterYear === yearStat.year }"
              @click="setYear(yearStat.year)"
            >
              {{ yearStat.year }} ({{ yearStat.count }})
            </button>
          </div>
        </div>
        
        <div class="sidebar-section" v-if="photoStore.filterYear">
          <h3>按月份</h3>
          <div class="month-list">
            <button 
              v-for="m in 12" 
              :key="m"
              class="month-btn"
              :class="{ active: photoStore.filterMonth === m }"
              @click="setMonth(m)"
            >
              {{ monthNames[m-1] }}
            </button>
          </div>
          <button class="clear-month-btn" @click="setMonth(null)">
            清除月份筛选
          </button>
        </div>
        
        <div class="sidebar-section">
          <h3>按评分</h3>
          <div class="score-filters">
            <button 
              class="score-btn"
              :class="{ active: photoStore.filterMemoryScoreMin === 80 }"
              @click="toggleMemoryScore(80)"
            >
              回忆分 ≥ 80
            </button>
            <button 
              class="score-btn"
              :class="{ active: photoStore.filterAestheticScoreMin === 80 }"
              @click="toggleAestheticScore(80)"
            >
              美观分 ≥ 80
            </button>
          </div>
        </div>
        
        <div class="sidebar-section">
          <h3>其他</h3>
          <button 
            class="quick-filter-btn"
            :class="{ active: photoStore.filterHasCaption }"
            @click="toggleCaption"
          >
            有文案的照片 ({{ photoStore.stats?.with_caption_count || 0 }})
          </button>
        </div>
        
        <div class="sidebar-section" v-if="hasActiveFilters">
          <button class="clear-all-btn" @click="photoStore.clearFilters()">
            清除所有筛选
          </button>
        </div>
      </aside>
      
      <main class="main-content">
        <div class="active-filters" v-if="hasActiveFilters">
          <span class="filter-tag" v-if="photoStore.filterYear">
            {{ photoStore.filterYear }}年
            <button @click="setYear(null)">×</button>
          </span>
          <span class="filter-tag" v-if="photoStore.filterMonth">
            {{ monthNames[photoStore.filterMonth-1] }}
            <button @click="setMonth(null)">×</button>
          </span>
          <span class="filter-tag" v-if="photoStore.filterMemoryScoreMin">
            回忆分≥{{ photoStore.filterMemoryScoreMin }}
            <button @click="toggleMemoryScore(null)">×</button>
          </span>
          <span class="filter-tag" v-if="photoStore.filterAestheticScoreMin">
            美观分≥{{ photoStore.filterAestheticScoreMin }}
            <button @click="toggleAestheticScore(null)">×</button>
          </span>
          <span class="filter-tag" v-if="photoStore.filterHasCaption">
            有文案
            <button @click="toggleCaption">×</button>
          </span>
        </div>
        
        <div class="photo-grid" v-if="photoStore.photos.length > 0">
          <div 
            v-for="photo in photoStore.photos" 
            :key="photo.id"
            class="photo-item"
            :class="{ 'analyzed': photo.status === 'analyzed' }"
            @click="viewPhoto(photo)"
          >
            <div class="photo-thumb">
              <img
                :src="`/api/photos/${photo.id}/file`"
                :alt="photo.filename"
                loading="lazy"
                @load="event => event.target.style.opacity = 1"
                @error="handleImageError($event, photo)"
              />
              <div class="placeholder">
                <span>{{ photo.filename.slice(0, 2) }}</span>
              </div>
              <div class="status-badge" :class="photo.status">
                {{ statusText[photo.status] }}
              </div>
            </div>
            <div class="photo-info">
              <p class="caption">{{ photo.caption || '暂无文案' }}</p>
              <p class="meta">
                {{ formatDate(photo.taken_at) }}
                <span v-if="photo.memory_score" class="score">
                  ⭐ {{ photo.memory_score.toFixed(1) }}
                </span>
              </p>
            </div>
          </div>
        </div>
        
        <div v-else-if="photoStore.loading" class="loading">
          加载中...
        </div>
        
        <div v-else class="empty">
          <p>暂无照片</p>
          <button class="btn btn-primary" @click="$router.push('/')">
            去扫描照片
          </button>
        </div>
        
        <!-- 分页 -->
        <div class="pagination" v-if="photoStore.total > photoStore.pageSize">
          <button 
            :disabled="photoStore.currentPage === 1"
            @click="changePage(photoStore.currentPage - 1)"
          >
            上一页
          </button>
          <span>{{ photoStore.currentPage }} / {{ totalPages }}</span>
          <button 
            :disabled="photoStore.currentPage >= totalPages"
            @click="changePage(photoStore.currentPage + 1)"
          >
            下一页
          </button>
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePhotoStore } from '@/stores/photos'

export default {
  name: 'Gallery',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const photoStore = usePhotoStore()
    
    const showSidebar = ref(true)
    
    const monthNames = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
    
    const hasActiveFilters = computed(() => {
      return photoStore.filterYear || 
             photoStore.filterMonth || 
             photoStore.filterMemoryScoreMin ||
             photoStore.filterAestheticScoreMin ||
             photoStore.filterHasCaption
    })

    const statusText = {
      pending: '待分析',
      analyzing: '分析中',
      analyzed: '已完成',
      duplicate: '重复',
      error: '错误'
    }

    const sortLabels = {
      memory_score: '↓ 回忆分',
      aesthetic_score: '↓ 美观分'
    }

    const totalPages = computed(() =>
      Math.ceil(photoStore.total / photoStore.pageSize)
    )

    onMounted(() => {
      // 检查 URL query 参数
      if (route.query.sort) {
        photoStore.sortBy = route.query.sort
      }
      if (route.query.page) {
        photoStore.currentPage = parseInt(route.query.page)
      }
      photoStore.fetchPhotos()
      photoStore.fetchStats()
    })

    const setYear = (year) => {
      photoStore.setYearFilter(year)
    }
    
    const setMonth = (month) => {
      photoStore.setMonthFilter(month)
    }
    
    const toggleMemoryScore = (min) => {
      if (photoStore.filterMemoryScoreMin === min) {
        photoStore.setScoreFilter('memory', null, null)
      } else {
        photoStore.setScoreFilter('memory', min, 100)
      }
    }
    
    const toggleAestheticScore = (min) => {
      if (photoStore.filterAestheticScoreMin === min) {
        photoStore.setScoreFilter('aesthetic', null, null)
      } else {
        photoStore.setScoreFilter('aesthetic', min, 100)
      }
    }
    
    const toggleCaption = () => {
      photoStore.setHasCaptionFilter(!photoStore.filterHasCaption)
    }

    const applyFilter = () => {
      photoStore.setFilter(photoStore.filterStatus)
    }

    const changePage = (page) => {
      photoStore.currentPage = page
      photoStore.fetchPhotos()
      // 更新 URL 的 page 参数
      router.push({
        path: '/gallery',
        query: { ...route.query, page: page }
      })
    }

    const onSortChange = () => {
      photoStore.setSort(photoStore.sortBy)
    }

    const viewPhoto = (photo) => {
      router.push(`/print/${photo.id}`)
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return '未知日期'
      const date = new Date(dateStr)
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const handleImageError = (event, photo) => {
      const img = event.target
      const retryCount = parseInt(img.dataset.retryCount || '0')
      
      if (retryCount < 2) {
        // 重试，添加时间戳避免缓存
        img.dataset.retryCount = (retryCount + 1).toString()
        setTimeout(() => {
          img.src = img.src.split('?')[0] + '?retry=' + Date.now()
        }, 500)
      }
      // 重试失败后图片保持透明，显示下面的 placeholder
    }

    const resetErrorPhotos = async () => {
      const errorPhotos = photoStore.photos.filter(p => p.status === 'error')
      if (errorPhotos.length === 0) {
        alert('当前页面没有错误照片')
        return
      }
      
      const confirmed = confirm(`确定要重置 ${errorPhotos.length} 张分析失败的照片吗？\n重置后它们将重新变为"待分析"状态。`)
      if (!confirmed) return
      
      let successCount = 0
      let failCount = 0
      
      for (const photo of errorPhotos) {
        try {
          await photoStore.reanalyzePhoto(photo.id)
          successCount++
        } catch (e) {
          failCount++
          console.error(`重置照片 ${photo.id} 失败:`, e)
        }
      }
      
      alert(`重置完成！\n成功: ${successCount} 张\n失败: ${failCount} 张\n\n请刷新页面查看。`)
      photoStore.fetchPhotos()
    }

    return {
      photoStore,
      statusText,
      sortLabels,
      totalPages,
      showSidebar,
      monthNames,
      hasActiveFilters,
      applyFilter,
      changePage,
      onSortChange,
      viewPhoto,
      formatDate,
      handleImageError,
      resetErrorPhotos,
      setYear,
      setMonth,
      toggleMemoryScore,
      toggleAestheticScore,
      toggleCaption
    }
  }
}
</script>

<style scoped>
.gallery {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 40px;
}

.gallery-header {
  background: white;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  position: sticky;
  top: 0;
  z-index: 10;
}

.back-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
}

.gallery-header h1 {
  font-size: 18px;
  font-weight: 600;
  flex: 1;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-bar select {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  background: white;
}

.sort-indicator {
  font-size: 12px;
  color: #667eea;
  font-weight: 500;
}

.toggle-sidebar-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.toggle-sidebar-btn:hover {
  background: #5568d3;
}

.gallery-body {
  display: flex;
}

.sidebar {
  width: 220px;
  background: white;
  padding: 16px;
  border-right: 1px solid #eee;
  flex-shrink: 0;
}

.sidebar-section {
  margin-bottom: 20px;
}

.sidebar-section h3 {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
}

.year-list, .month-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.year-btn, .month-btn {
  padding: 8px 12px;
  border: 1px solid #eee;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  text-align: left;
  transition: all 0.2s;
}

.year-btn:hover, .month-btn:hover {
  background: #f5f5f5;
}

.year-btn.active, .month-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.clear-month-btn, .clear-all-btn {
  width: 100%;
  padding: 8px;
  margin-top: 8px;
  border: 1px dashed #ccc;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  color: #666;
}

.clear-month-btn:hover, .clear-all-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.score-filters {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.score-btn {
  padding: 8px 12px;
  border: 1px solid #eee;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.score-btn:hover {
  background: #f5f5f5;
}

.score-btn.active {
  background: #f59e0b;
  color: white;
  border-color: #f59e0b;
}

.quick-filter-btn {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #eee;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  text-align: left;
  transition: all 0.2s;
}

.quick-filter-btn:hover {
  background: #f5f5f5;
}

.quick-filter-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.main-content {
  flex: 1;
  min-width: 0;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #eee;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #667eea;
  color: white;
  border-radius: 16px;
  font-size: 12px;
}

.filter-tag button {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 0;
  font-size: 14px;
  line-height: 1;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  padding: 16px;
}

.photo-item {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.photo-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.photo-thumb {
  position: relative;
  aspect-ratio: 1;
  background: #f0f0f0;
  overflow: hidden;
}

.photo-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  opacity: 0;
  transition: opacity 0.3s ease;
  position: relative;
  z-index: 1;
}

.placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 24px;
  z-index: 0;
}

.status-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.status-badge.pending {
  background: #fff3cd;
  color: #856404;
}

.status-badge.analyzed {
  background: #d4edda;
  color: #155724;
}

.status-badge.duplicate {
  background: #f8d7da;
  color: #721c24;
}

.status-badge.error {
  background: #dc3545;
  color: white;
  font-weight: bold;
}

.reset-error-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  margin-left: 10px;
  font-weight: 500;
}

.reset-error-btn:hover {
  background: #c82333;
}

.photo-info {
  padding: 12px;
}

.caption {
  font-size: 13px;
  line-height: 1.4;
  color: #333;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.meta {
  font-size: 11px;
  color: #999;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score {
  color: #f59e0b;
  font-weight: 600;
}

.loading, .empty {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty .btn {
  margin-top: 20px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
  padding: 20px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .photo-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    padding: 12px;
  }
}
</style>
