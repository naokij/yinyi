# AGENTS.md - AI Agent Guidelines for YinYi Project

This file provides guidelines for AI coding agents working on the YinYi project.

---

## 1. Project Overview

**YinYi (印忆)** - AI Photo Memory Printing Assistant
- Backend: Python FastAPI (port 8765)
- Frontend: Vue3 + Vite (port 3000)
- Database: SQLite (`backend/data/yinyi.db`)
- AI Support: Ollama (local), Iflow API (cloud), vLLM

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

1. **Environment Variables**: Never commit `.env` files
2. **Data Files**: `backend/data/` and `backend/exports/` are gitignored
3. **HEIC Support**: Uses Pillow + pillow-heif for conversion
4. **AI Backends**: Supports Ollama (local), Iflow (cloud API), vLLM
5. **Database**: SQLite - backup by copying `yinyi.db` file
6. **Startup Scripts**: Use `start-windows.bat` and `stop-windows.bat` for Windows
7. **LAN Access**: Add `--host 0.0.0.0` for frontend, configure firewall for ports 3000 and 8765
8. **Restart Protection**: Photos stuck in `analyzing` status are auto-reset on startup

---

*Last updated: 2026-02-14*
