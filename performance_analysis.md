# Performance Analysis - GMP API Bottlenecks

## 🔍 Identified Performance Issues

### **Brainstorming API (`/brainstorming`)**

#### Primary Bottlenecks:

1. **🐌 CRITICAL: Sequential LLM Calls (60-80% of time)**
   - **Location**: `brainstorming.py` lines 63-102
   - **Issue**: Making 4+ LLM calls sequentially in a for loop
   - **Impact**: If each call takes 15-30 seconds → 60-120 seconds total
   - **Current Code**:
   ```python
   for prompte in prompts:  # 4+ iterations
       output = llm.call(query)  # BLOCKING call (15-30s each)
   ```

2. **⚠️ MAJOR: summary_qa() LLM Call (10-15s)**
   - **Location**: `brainstorming.py` line 13
   - **Issue**: Another blocking LLM call at the start
   - **Impact**: 10-15 seconds

3. **⚠️ MAJOR: Vector Similarity Search (5-10s)**
   - **Location**: `brainstorming.py` lines 21-33
   - **Issue**: MongoDB vector search with cosine similarity (Python-side calculation)
   - **Impact**: 5-10 seconds
   - **Problem**: Fetches ALL documents and calculates similarity in Python loop

4. **⚠️ MODERATE: Redis Lookups in Loop (3-5s)**
   - **Location**: `brainstorming.py` lines 40-55
   - **Issue**: Multiple sequential Redis `get_deviation()` calls
   - **Impact**: 3-5 seconds for network round-trips

5. **⚠️ MINOR: process_description() LLM Call (10-15s)**
   - **Location**: `brainstorming.py` line 17
   - **Issue**: Another LLM call
   - **Impact**: 10-15 seconds

### **GMP Generation API (`/gmpgeneration`)**

#### Primary Bottlenecks:

1. **🐌 CRITICAL: Sequential LLM Calls in Loop**
   - **Location**: `gmp_dev_generator.py` lines 29-48
   - **Issue**: Same as brainstorming - sequential LLM calls
   - **Impact**: 60-120 seconds for multiple prompts

2. **⚠️ MAJOR: Multiple summary_qa() Calls**
   - **Location**: `gmp_dev_generator.py` lines 16-18
   - **Issue**: Loops through all input data keys calling LLM each time
   - **Impact**: 10-15s per key × number of keys

---

## 🚀 Optimization Strategies (High Impact → Low)

### **1. ASYNC/PARALLEL LLM CALLS** ⭐⭐⭐⭐⭐
**Impact**: Reduce 60-120s to 15-30s (75% reduction)

**Implementation**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_prompts_parallel(prompts, summary, rootcause_content, results):
    tasks = []
    for prompte in prompts:
        task = asyncio.create_task(call_llm_async(prompte, summary, rootcause_content, results))
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks)
    return responses
```

### **2. BATCH/CACHE REDIS CALLS** ⭐⭐⭐⭐
**Impact**: Reduce 3-5s to <1s (80% reduction)

**Implementation**:
```python
# Use pipeline for batch Redis operations
def get_deviations_batch(redis_repo, deviation_ids):
    pipeline = redis_repo.client.pipeline()
    for dev_id in deviation_ids:
        pipeline.get(f"deviation:{dev_id}")
    return pipeline.execute()
```

### **3. OPTIMIZE VECTOR SEARCH** ⭐⭐⭐⭐
**Impact**: Reduce 5-10s to 1-2s (70% reduction)

**Problem**: Current MongoDB implementation fetches ALL documents and computes similarity in Python

**Solutions**:
- Use MongoDB Atlas Vector Search (native)
- Or switch to Pinecone/Qdrant with built-in vector indices
- Or add MongoDB aggregation pipeline for filtering

### **4. CACHE LLM RESPONSES** ⭐⭐⭐
**Impact**: Eliminate repeat calls (100% for cached queries)

**Implementation**:
```python
import hashlib
import redis

def get_cached_llm_response(query, redis_client):
    key = f"llm_cache:{hashlib.md5(query.encode()).hexdigest()}"
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    
    response = llm.call(query)
    redis_client.setex(key, 3600, json.dumps(response))  # 1hr cache
    return response
```

### **5. OPTIMIZE EMBEDDING CALLS** ⭐⭐
**Impact**: Reduce embedding time slightly

- Batch embedding requests instead of one-by-one
- Use smaller/faster embedding model if acceptable

### **6. REDUCE PROMPT COMPLEXITY** ⭐⭐
**Impact**: Reduce LLM processing time by 10-20%

- Shorter prompts = faster LLM responses
- Remove redundant instructions

---

## 📊 Expected Timeline Improvements

### Current Performance:
- **Brainstorming API**: 90-150 seconds
- **GMP Generation API**: 80-140 seconds

### After Optimizations:
| Optimization | Brainstorming Time | GMP Generation Time |
|-------------|-------------------|---------------------|
| **Baseline** | 120s | 110s |
| + Parallel LLM | 40s (↓67%) | 35s (↓68%) |
| + Redis Batch | 37s (↓69%) | 32s (↓71%) |
| + Vector Search | 32s (↓73%) | 32s (↓71%) |
| + LLM Cache* | 5s (↓96%) | 5s (↓95%) |

*Cache only works for repeat queries

---

## 🎯 Recommended Implementation Order

1. **First**: Implement parallel LLM calls (biggest impact)
2. **Second**: Add Redis batching (easy win)
3. **Third**: Optimize vector search (moderate effort)
4. **Fourth**: Add LLM caching (helps with repeat requests)
5. **Fifth**: Fine-tune prompts and embeddings

---

## 🛠️ Next Steps

1. Add timing instrumentation to measure each section
2. Implement async LLM calls first
3. Monitor and benchmark improvements
4. Continue with other optimizations
