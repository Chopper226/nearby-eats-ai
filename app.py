from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

import requests
from datetime import datetime

from schemas import Request
from recommender import Recommender
from config import LAB_MODEL,GOOGLE_MAPS_API_KEY,LAB_OLLAMA_API

app = FastAPI(
    title="附近吃吃推薦"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 初始化
recommender = Recommender()


# API 端點
@app.get("/")
async def root():
    return {
        "service": "附近吃吃推薦 API",
        "status": "running",
        "ai_api": "實驗室 Ollama API",
        "ai_model": LAB_MODEL,
        "features": "完整詳細推薦、加強內容生成、WebUI優化",
        "endpoints": {
            "GET /": "API 資訊",
            "POST /api/recommend": "取得推薦",
            "POST /api/recommend_full": "取得完整推薦（WebUI專用）",
            "GET /api/health": "健康檢查",
            "GET /api/test_ai": "測試 AI 連接"
        }
    }

@app.post("/api/recommend")
async def get_recommendation(request: Request, background_tasks: BackgroundTasks):
    """取得推薦"""
    
    # 檢查快取
    cached_result = recommender.cache.get(request.question, request.location)
    if cached_result:
        print(f"📦 使用快取結果")
        # 檢查快取內容是否足夠詳細
        if 'recommendation' in cached_result and len(cached_result['recommendation']) < 600:
            print(f"⚠️ 快取內容較短，重新取得")
            cached_result = None
    
    if not cached_result:
        try:
            print(f"🔄 處理新請求: {request.question}")
            print(f"📍 位置: {request.location}")
            print(f"📏 範圍: {request.radius}m, 數量: {request.max_results}")
            
            # 取得推薦
            result = await recommender.get_recommendation(
                request.question,
                request.location,
                request.radius,
                request.max_results
            )
            
            # 儲存到快取
            background_tasks.add_task(
                recommender.cache.set,
                request.question,
                request.location,
                result
            )
            
            return {
                "source": "fresh",
                **result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ 推薦錯誤: {e}")
            raise HTTPException(status_code=500, detail=f"推薦服務錯誤: {str(e)}")
    
    return {
        "source": "cache",
        "cached_at": cached_result.get("timestamp"),
        **cached_result
    }

@app.post("/api/recommend_full")
async def get_recommendation_full(request: Request, background_tasks: BackgroundTasks):
    """取得完整推薦 - 專為 WebUI 設計，確保顯示完整內容"""
    
    print(f"\n" + "="*60)
    print(f"🌐 WebUI 專用請求: {request.question}")
    print(f"="*60)
    
    # 檢查快取
    cached_result = recommender.cache.get(request.question, request.location)
    
    # 強制重新取得，確保內容完整
    if cached_result:
        # 檢查快取內容長度
        rec_length = cached_result.get('recommendation_length', 0) if 'recommendation_length' in cached_result else len(cached_result.get('recommendation', ''))
        print(f"📦 快取內容長度: {rec_length}")
        
        # 如果內容不夠詳細，重新取得
        if rec_length < 1000:
            print(f"⚠️ 快取內容可能不夠詳細，重新取得")
            cached_result = None
        else:
            print(f"✅ 使用快取內容")
    
    if not cached_result:
        try:
            print(f"🔄 處理新請求")
            
            # 取得推薦
            result = await recommender.get_recommendation(
                request.question,
                request.location,
                request.radius,
                request.max_results
            )
            
            # 儲存到快取
            background_tasks.add_task(
                recommender.cache.set,
                request.question,
                request.location,
                result
            )
            
            response_data = {
                "source": "fresh",
                **result
            }
            
        except Exception as e:
            print(f"❌ 推薦錯誤: {e}")
            raise HTTPException(status_code=500, detail=f"推薦服務錯誤: {str(e)}")
    else:
        response_data = {
            "source": "cache",
            "cached_at": cached_result.get("timestamp"),
            **cached_result
        }
    
    # 為 WebUI 優化 - 確保結構正確
    recommendation = response_data.get('recommendation', '')
    
    # 如果內容不足，添加更多詳細建議
    if len(recommendation) < 500:
        print(f"⚠️ 內容可能不夠詳細 ({len(recommendation)} 字)，添加補充")
        
        extra_content = """

## 🔍 詳細補充分析

### 📊 綜合評估指標
1. **評分可靠性**：4.5星以上為優質選擇
2. **評價數量**：100+評價較有參考價值
3. **近期評論**：查看最近30天評價
4. **照片真實性**：用戶上傳照片 vs 官方照片

### 🎯 選擇策略
- **追求品質**：優先選擇評分4.5+餐廳
- **預算考量**：根據價格等級選擇
- **時間安排**：避開用餐高峰時段
- **特殊需求**：確認餐廳是否滿足特殊需求

### 💡 實用小技巧
1. **預約確認**：熱門時段建議提前1-2天預約
2. **交通規劃**：使用Google Maps規劃最佳路線
3. **備選方案**：準備1-2家備選餐廳
4. **評價驗證**：查看多個平台的評價

### ⚠️ 注意事項
1. **營業時間**：部分餐廳可能有臨時店休
2. **價格變動**：菜單價格可能調整
3. **服務變化**：服務品質可能因時段而異
4. **環境因素**：週末可能較為擁擠

祝您用餐愉快！ 🍽️✨"""
        
        response_data['recommendation'] = recommendation + extra_content
        response_data['metadata']['recommendation_length'] = len(response_data['recommendation'])
        print(f"📝 補充後總長度: {len(response_data['recommendation'])} 字元")
    
    print(f"\n📤 返回完整推薦內容")
    print(f"   - 總長度: {len(response_data.get('recommendation', ''))} 字元")
    print(f"   - 餐廳數量: {len(response_data.get('restaurants', []))}")
    print(f"="*60)
    
    return response_data

@app.get("/api/health")
async def health_check():
    """健康檢查"""
    try:
        test_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": "台北", "key": GOOGLE_MAPS_API_KEY}
        response = requests.get(test_url, params=params, timeout=5)
        google_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        google_status = "unreachable"
    
    ai_status = "healthy" if recommender.chat_handler.test_connection() else "unreachable"
    
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "google_maps": google_status,
            "ai_api": ai_status,
            "cache_db": "healthy"
        },
        "version": "6.2.0",
        "features": ["完整推薦內容", "詳細分析", "WebUI 專用端點"]
    }

@app.get("/api/test_ai")
async def test_ai_connection():
    """測試 AI API 連接"""
    if recommender.chat_handler.test_connection():
        return {
            "status": "success",
            "message": "實驗室 Ollama API 連接正常",
            "model": LAB_MODEL,
            "capabilities": "完整詳細推薦生成"
        }
    else:
        raise HTTPException(
            status_code=503,
            detail=f"無法連接到實驗室 Ollama API"
        )

@app.get("/api/debug")
async def debug_info():
    """除錯資訊"""
    cursor = recommender.cache.conn.cursor()
    
    # 取得快取統計
    cursor.execute("SELECT COUNT(*) FROM cache")
    total_entries = cursor.fetchone()[0]
    
    cursor.execute(
        "SELECT COUNT(*) FROM cache WHERE expires_at > ?", 
        (datetime.now().isoformat(),)
    )
    valid_entries = cursor.fetchone()[0]
    
    # 取得最近一筆快取
    cursor.execute(
        "SELECT question, location, LENGTH(response) as resp_len FROM cache ORDER BY created_at DESC LIMIT 1"
    )
    latest_cache = cursor.fetchone()
    
    latest_info = None
    if latest_cache:
        latest_info = {
            "question": latest_cache[0],
            "location": latest_cache[1],
            "response_length": latest_cache[2]
        }
    
    return {
        "current_time": datetime.now().isoformat(),
        "cache_stats": {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "latest_cache": latest_info
        },
        "config": {
            "ai_api_url": LAB_OLLAMA_API,
            "ai_model": LAB_MODEL,
            "google_maps_key_set": bool(GOOGLE_MAPS_API_KEY)
        },
        "version": "6.2.0",
        "webui_endpoint": "/api/recommend_full"
    }