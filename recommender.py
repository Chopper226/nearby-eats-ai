import time
from datetime import datetime
from typing import List, Dict
from fastapi import HTTPException

from cache import QueryCache
from clients.llmClient import ChatAPIHandler
from clients.mapsClient import GoogleMapsSearcher
from config import LAB_MODEL


class Recommender:
    def __init__(self):
        self.cache = QueryCache()
        self.maps_searcher = GoogleMapsSearcher()
        self.chat_handler = ChatAPIHandler()
        
        if self.chat_handler.test_connection():
            print("✅ 實驗室 Ollama API 連接成功")
        else:
            print("⚠️  實驗室 Ollama API 連接失敗")
    
    def build_analysis_prompt(self, question: str, location: str, restaurants: List[Dict]) -> str:
        """構建分析提示詞 - 加強內容要求"""
        
        high_rated_restaurants = [r for r in restaurants if r.get('rating', 0) >= 4.5]
        
        restaurant_info = []
        for i, r in enumerate(restaurants, 1):
            info = f"{i}. **{r.get('name', '未知名稱')}**"
            
            rating = r.get('rating', 0)
            if rating >= 4.5:
                info += " 🏆 **高評價推薦**"
            elif rating >= 4.0:
                info += " 👍 **好評餐廳**"
            
            info += f"\n   地址：{r.get('address', '地址不明')}\n"
            
            if rating:
                stars = "⭐" * int(rating)
                info += f"   評分：{rating}/5 {stars}"
                if rating >= 4.5:
                    info += " **(高評價!)**"
                info += "\n"
            
            if r.get('price_level'):
                price_symbols = '💰' * r['price_level']
                info += f"   價格等級：{price_symbols} ({r['price_level']}/4)\n"
            
            if r.get('open_now') is not None:
                status = "🟢 **營業中**" if r['open_now'] else "🔴 休息中"
                info += f"   狀態：{status}\n"
            
            restaurant_info.append(info)
        
        # 加強提示詞，要求更多內容
        prompt = f"""你是一個專業的台灣美食推薦專家。請根據以下搜尋結果，為使用者提供詳細的推薦分析。

                ## 📍 搜尋位置：{location}
                ## ❓ 使用者需求：{question}

                ## 📊 搜尋結果統計：
                - 總共找到 {len(restaurants)} 家餐廳
                - **高評價餐廳**（4.5星以上）：{len(high_rated_restaurants)} 家
                - **推薦優先考慮高評價餐廳**，品質更有保障！

                ## 🏪 餐廳詳細資訊：
                {chr(10).join(restaurant_info)}

                ## 📝 請提供非常詳細的分析（至少1200字）：

                ### 1. 推薦排名（前3名）
                請詳細說明為什麼推薦這幾家，每家至少100字說明：
                - 第一推薦：詳細理由、特色、適合人群
                - 第二推薦：詳細理由、特色、適合人群  
                - 第三推薦：詳細理由、特色、適合人群

                ### 2. 高評價餐廳深度分析
                針對評分4.5星以上的每家餐廳：
                - 餐廳名稱（評分）
                - 3-5個具體優點
                - 最適合什麼樣的人
                - 必點菜色或特色
                - 用餐建議（最佳時段、注意事項）

                ### 3. 拍照與環境完整評估
                針對每家推薦餐廳：
                - 拍照友好度評分（1-5星）
                - 最佳拍照點和角度
                - 推薦拍照時段
                - 環境特色描述
                - Instagram 打卡建議

                ### 4. 實用資訊詳解
                1. **交通指南**：從 {location} 出發的詳細路線
                2. **營業時間**：每家餐廳的營業時間建議
                3. **價格分析**：每家餐廳的價格範圍和CP值
                4. **預約策略**：是否需要預約、如何預約
                5. **停車資訊**：附近停車選擇

                ### 5. 根據使用者需求特別建議
                針對「{question}」需求：
                - 哪家餐廳最符合？為什麼？
                - 特別推薦的體驗方式
                - 避開的潛在問題

                ### 6. 完整總結與最終建議
                - 綜合比較表格
                - 不同情境下的最佳選擇
                - 最終推薦排名
                - 重要注意事項提醒

                ## 回答要求：
                - 使用繁體中文，語氣親切但專業
                - 確保內容完整詳細，至少700字以上
                - 結構清晰，分段明確
                - 提供具體、可執行的建議

                請開始你的專業推薦分析："""
        
        return prompt
    
    async def get_recommendation(self, question: str, location: str, radius: int, max_results: int) -> Dict:
        """取得推薦"""
        start_time = time.time()
        
        print(f"\n" + "="*60)
        print(f"🔍 開始搜尋: {question}")
        print(f"📍 位置: {location}")
        print(f"📏 範圍: {radius}m, 數量: {max_results}")
        
        # 1. 搜尋 Google Maps
        lat, lng = self.maps_searcher.get_coordinates(location)
        if not lat or not lng:
            raise HTTPException(status_code=400, detail=f"無法找到地點: {location}")
        
        keywords = self._extract_keywords(question)
        search_keyword = keywords[0] if keywords else "餐廳"
        
        print(f"📍 座標: {lat}, {lng}, 關鍵字: {search_keyword}")
        
        restaurants = self.maps_searcher.search_restaurants(
            lat, lng, search_keyword, radius, max_results
        )
        
        if not restaurants:
            raise HTTPException(status_code=404, detail="找不到符合條件的餐廳")
        
        restaurants.sort(key=lambda x: x.get('rating', 0), reverse=True)
        
        search_time = time.time() - start_time
        print(f"✅ 找到 {len(restaurants)} 家餐廳 (搜尋時間: {search_time:.1f}秒)")
        
        # 統計高評分餐廳
        high_rated = len([r for r in restaurants if r.get('rating', 0) >= 4.5])
        print(f"⭐ 高評價餐廳（4.5星以上）: {high_rated} 家")
        
        # 2. 構建分析提示詞
        prompt = self.build_analysis_prompt(question, location, restaurants)
        print(f"📝 提示詞長度: {len(prompt)} 字元")
        
        # 3. 呼叫實驗室 Ollama API 進行分析
        print("🤖 呼叫實驗室 Ollama API 進行分析...")
        analysis_start = time.time()
        llm_response = self.chat_handler.call_chat_api(prompt)
        analysis_time = time.time() - analysis_start
        
        print(f"📊 AI 分析完成 (時間: {analysis_time:.1f}秒)")
        print(f"📝 AI回應長度: {len(llm_response)} 字元")
        
        # 檢查回應是否足夠詳細
        if len(llm_response) < 600:
            print(f"⚠️ AI回應可能不夠詳細 ({len(llm_response)} 字)")
        
        # 4. 準備回應 - 確保 recommendation 欄位有完整內容
        result = {
            "question": question,
            "location": location,
            "restaurants_count": len(restaurants),
            "high_rated_count": high_rated,
            "recommendation": llm_response,
            "restaurants": [
                {
                    "name": r.get('name'),
                    "address": r.get('address'),
                    "rating": r.get('rating'),
                    "price_level": r.get('price_level'),
                    "open_now": r.get('open_now'),
                    "source": r.get('source'),
                    "is_high_rated": r.get('rating', 0) >= 4.5
                }
                for r in restaurants
            ],
            "metadata": {
                "search_time": round(search_time, 2),
                "analysis_time": round(analysis_time, 2),
                "total_time": round(time.time() - start_time, 2),
                "search_keyword": search_keyword,
                "high_rated_threshold": 4.5,
                "ai_model": LAB_MODEL,
                "ai_source": "實驗室 Ollama",
                "has_recommendation": True,
                "recommendation_length": len(llm_response),
                "is_detailed": len(llm_response) >= 600  # 標記是否詳細
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # 打印詳細檢查信息
        print(f"\n" + "="*60)
        print(f"📦 結果檢查")
        print(f"="*60)
        print(f"✅ recommendation存在: {'recommendation' in result}")
        print(f"📏 recommendation長度: {len(result['recommendation'])} 字元")
        print(f"🏪 restaurants數量: {len(result['restaurants'])}")
        print(f"⭐ 高評價餐廳: {result['high_rated_count']} 家")
        print(f"⏱️  總處理時間: {result['metadata']['total_time']} 秒")
        print(f"="*60 + "\n")
        
        return result
    
    def _extract_keywords(self, question: str) -> List[str]:
        """提取搜尋關鍵字"""
        stop_words = ["我想找", "我想吃", "我想去", "推薦", "哪裡有", "哪裡可以", "的", "附近"]
        
        simplified = question
        for word in stop_words:
            simplified = simplified.replace(word, '')
        
        keywords = []
        
        brunch_words = ["早午餐", "早餐", "brunch","午餐","晚餐","消夜","宵夜", "咖啡", "咖啡廳", "餐廳", "輕食", "蛋料理", "吐司", "鬆餅","小吃","甜點","甜品","冰","燒烤","燒肉","速食"]
        for word in brunch_words:
            if word in simplified:
                keywords.append(word)
        
        requirement_words = ["拍照", "健康", "安靜", "平價", "便宜", "高級", "戶外", "座位", "看書", "約會", "聚餐"]
        for word in requirement_words:
            if word in simplified:
                keywords.append(word)
        
        if not keywords and simplified.strip():
            keywords = [simplified.strip()[:20]]
        
        return keywords[:3]