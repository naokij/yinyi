# AGENTS.md - AI Agent Guidelines for YinYi Project

This file provides guidelines for AI coding agents working on the YinYi project.

---

## 1. Project Overview

**YinYi (印忆)** - AI Photo Memory Printing Assistant
- Backend: Python FastAPI (port 8765) — single-process, also serves frontend `dist`
- Frontend: Vue3 + Vite (built to `frontend/dist`, served by FastAPI in production)
- Database: SQLite (`backend/data/yinyi.db`)
- AI Backends: **Agnes `agnes-2.0-flash` (current, free)**, Iflow API, Ollama, vLLM
- Deployment: Linux + systemd (no Docker, no nginx for LAN use)

---

## 2. Build & Run Commands

### Backend

```bash
# Navigate to backend
cd backend

# Create/activate virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend
python main.py

# Backend runs on http://localhost:8765
# API docs at http://localhost:8765/docs
```

### Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Frontend runs on http://localhost:3000
```

### Running Tests

Currently, **no formal test suite exists**. To add tests:

```bash
# Backend - pytest (add to requirements.txt first)
pip install pytest pytest-asyncio
pytest                          # run all tests
pytest tests/test_file.py       # run specific test file
pytest -k "test_name"          # run tests matching pattern

# Frontend - vitest (add to package.json first)
npm install -D vitest
npx vitest run                  # run all tests
npx vitest run test_file.js     # run specific test
```

### Linting (To Be Added)

```bash
# Python - ruff (recommended)
pip install ruff
ruff check .                   # check all files
ruff check --fix .             # check and fix
ruff format .                  # format code

# JavaScript/Vue - ESLint + Prettier (add to package.json)
npm install -D eslint prettier
npx eslint src/                # lint frontend
npx prettier --write src/     # format frontend
```

---

## 3. Code Style Guidelines

### Python (Backend)

#### Imports
- Standard library first, then third-party, then local
- Use absolute imports within backend package
- Group: stdlib → external → local, with blank lines between groups
```python
# Good
import os
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from config import settings
from database import get_db, Photo
```

#### Formatting
- Line length: 100 characters max
- Indentation: 4 spaces
- Use Black formatter for consistent style
- Type hints required for function parameters and return values

#### Naming Conventions
- **Files**: snake_case (e.g., `ai_analyzer.py`, `cache_manager.py`)
- **Classes**: PascalCase (e.g., `PhotoResponse`, `HEICCacheManager`)
- **Functions/variables**: snake_case (e.g., `get_photo`, `photo_id`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_CACHE_SIZE_GB`)
- **Private functions**: prefix with underscore (e.g., `_internal_function`)

#### Type Hints
```python
# Required for public functions
from typing import Optional, List

def get_photo(photo_id: int, db: Session) -> Optional[PhotoResponse]:
    ...

def list_photos(
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "taken_at"
) -> PhotoListResponse:
    ...
```

#### Error Handling
- Use HTTPException for API errors with appropriate status codes
- Log errors before raising
- Include user-friendly error messages
```python
# Good
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=400, detail=f"操作失败: {str(e)}")
```

#### Async/Await
- Use async for I/O-bound operations (API calls, file I/O)
- Keep async functions non-blocking
```python
# Good - async for I/O
async def fetch_photos():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

# Avoid - CPU-bound in async (use run_in_executor)
async def process_heavy():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, cpu_heavy_function)
```

---

### JavaScript/Vue (Frontend)

#### Imports
- Use `@` alias for src directory
- Group: Vue/framework → external → local
```javascript
// Good
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { usePhotoStore } from '@/stores/photos'
import PhotoCard from '@/components/PhotoCard.vue'
```

#### Formatting
- Use 2 spaces for indentation
- Use semicolons (consistent with existing codebase)
- Prefer single quotes for strings

#### Naming Conventions
- **Components**: PascalCase (e.g., `PhotoGallery.vue`, `PhotoCard.vue`)
- **Composables/Stores**: camelCase (e.g., `usePhotos.js`, `photos.js`)
- **Constants**: UPPER_SNAKE_CASE
- **Props**: camelCase in JS, kebab-case in template

#### TypeScript (Recommended for New Code)
```typescript
// Use TypeScript for new components
interface Photo {
  id: number
  filename: string
  memory_score: number | null
  aesthetic_score: number | null
}

const props = defineProps<{
  photo: Photo
  size?: number
}>()
```

#### Vue Component Structure
```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
// imports

// props
const props = defineProps<{ /* ... */ }>()

// emits
const emit = defineEmits(['update', 'delete'])

// refs
const loading = ref(false)

// computed
const sortedPhotos = computed(() => /* ... */)

// methods
function handleClick() { /* ... */ }

// lifecycle
onMounted(() => { /* ... */ })
</script>

<template>
  <!-- template content -->
</template>

<style scoped>
/* scoped styles */
</style>
```

#### Error Handling
- Use try/catch with user feedback
- Show loading states during async operations
```javascript
async function fetchData() {
  loading.value = true
  try {
    const response = await api.getData()
    data.value = response.data
  } catch (error) {
    console.error('Failed to fetch:', error)
    errorMessage.value = '加载失败，请重试'
  } finally {
    loading.value = false
  }
}
```

---

## 4. API Design Guidelines

### RESTful Endpoints
- Use nouns for resources: `/photos`, `/analyze`, `/scanner`
- Use HTTP verbs appropriately: GET (read), POST (create), DELETE (remove)
- Return proper HTTP status codes

### Request/Response
```python
# Good - consistent response format
@router.get("/photos")
async def list_photos():
    return {
        "total": 100,
        "photos": [...],
        "page": 1,
        "page_size": 20
    }
```

---

## 5. Database Guidelines

### SQLAlchemy Models
- Use declarative base
- Define relationships using back_populates
- Add indexes for frequently queried columns
```python
class Photo(Base):
    __tablename__ = "photos"
    
    id = Column(Integer, primary_key=True)
    path = Column(String(500), unique=True, index=True)  # index for lookups
    filename = Column(String(255))
    
    analysis = relationship("Analysis", back_populates="photo", uselist=False)
```

---

## 6. File Organization

```
backend/
├── main.py              # FastAPI app entry
├── config.py            # Settings
├── database.py          # Models & DB connection
├── ai_analyzer.py       # AI logic
├── cache_manager.py     # HEIC cache
├── routers/             # API routes
│   ├── photos.py
│   ├── analyze.py
│   └── ...
└── data/                # Runtime data (not committed)
    ├── yinyi.db
    └── cache/

frontend/
├── src/
│   ├── views/           # Page components
│   ├── components/     # Reusable components
│   ├── stores/         # Pinia stores
│   ├── api/           # API clients
│   └── router/        # Vue Router
└── public/            # Static assets
```

---

## 7. Git Conventions

- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Keep commits atomic and focused
- Write descriptive commit messages
- Push to remote after completing features

---

## 8. Important Notes

1. **Environment Variables**: Never commit `.env` files (project root + symlinked to `backend/.env`)
2. **Data Files**: `backend/data/` and `backend/exports/` are gitignored
3. **HEIC Support**: Uses Pillow + pillow-heif for conversion
4. **AI Backends**: Agnes `agnes-2.0-flash` (free, default), Iflow API, Ollama, vLLM
5. **Database**: SQLite - backup by copying `yinyi.db` file
6. **Startup Scripts**: `start-windows.bat` / `stop-windows.bat` for Windows; systemd `yinyi-backend.service` for Linux
7. **LAN Access**: FastAPI binds `0.0.0.0:8765` by default; open firewall for 8765
8. **Restart Protection**: Photos stuck in `analyzing` status are auto-reset on startup
9. **NAS Thumbnail Skip**: `scanner.SKIP_DIRS` excludes Synology/QNAP system dirs (`@eaDir`, `@synorec`, `@tmp`, `@quarantine`, `@sharebin`, `#recycle`, `lost+found`) — do NOT remove
10. **AI Thinking Toggle** (env vars):
    - `ENABLE_THINKING=true` — score call uses thinking (default)
    - `ENABLE_CAPTION=true` — generate caption for high-score photos
    - `ENABLE_CAPTION_THINKING=false` — caption forces thinking off (open-ended task prone to infinite thinking loop)
    - `CAPTION_MIN_MEMORY=80` — only generate caption when memory_score >= 80
    - `MAX_CONCURRENT_API_CALLS=3` — semaphore limits API concurrency (Agnes free tier is 20 RPM, server-side serial)
    - `BATCH_WORKERS=3` — `ThreadPoolExecutor` workers for batch analyze
11. **AI Adapter Differences**:
    - **mimo (xiaomimimo)**: thinking is ON by default. Disable via `thinking: {"type": "disabled"}`. Reasoning field: `reasoning_content` + `usage.completion_tokens_details.reasoning_tokens`
    - **agnes (apihub.agnes-ai)**: thinking is OFF by default. Enable via `chat_template_kwargs: {"enable_thinking": true}`. Reasoning field: `provider_specific_fields.reasoning` + `message.reasoning_content`
12. **Frontend Served by Backend**: After `npm run build`, `dist/` is mounted at `/assets/...` and `/` returns `index.html`. Catch-all SPA fallback at `/{full_path:path}` for Vue Router history mode.
13. **NFS Mount**: `RequiresMountsFor=/mnt/nas/photos` in systemd unit; `/etc/fstab` line: `192.168.3.6:/volume1/homes/jiangle/Photos /mnt/nas/photos nfs defaults,_netdev,x-systemd.automount,x-systemd.requires=network-online.target,noatime 0 0`
14. **Nightly Restart Timer**: `yinyi-nightly-restart.timer` restarts service at 4:00 AM daily to flush memory/swap. Combined with lifespan auto-resume, this provides zero-downtime memory management.
15. **Memory Limit**: `MemoryMax=1G`, `MemoryHigh=768M` — glibc fragmentation causes gradual RSS growth; 1-worker config keeps growth slow; daily timer prevents swap buildup.

---

*Last updated: 2026-06-11*
