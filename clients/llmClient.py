import time
import requests
import json

from config import LAB_API_TOKEN, LAB_MODEL,LAB_OLLAMA_API

# 實驗室 Ollama
class ChatAPIHandler:
    """實驗室 Ollama API 處理器"""
    
    @staticmethod
    def call_chat_api(prompt: str) -> str:
        """呼叫實驗室 Ollama API"""
        
        try:
            print(f"🤖 呼叫實驗室 Ollama API...")
            
            headers = {
                "Authorization": f"Bearer {LAB_API_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # 增加 max_tokens 確保有足夠內容
            payload = {
                "model": LAB_MODEL,
                "prompt": prompt,
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 3500,  # 增加到 3500 tokens
                "top_p": 0.9,
                "stop": ["\n\n##", "### END", "====="]
            }
            
            start_time = time.time()
            response = requests.post(
                LAB_OLLAMA_API,
                headers=headers,
                json=payload,
                stream=True,
                timeout=180,  # 增加超時時間
                verify=False
            )
            
            print(f"📡 回應狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                full_response = ""
                chunk_count = 0
                
                for line in response.iter_lines():
                    if line:
                        chunk_count += 1
                        try:
                            line_str = line.decode('utf-8')
                            
                            if line_str.startswith("data: "):
                                line_str = line_str[6:]
                            
                            data = json.loads(line_str)
                            
                            if "response" in data:
                                full_response += data["response"]
                            
                            if data.get("done", False):
                                break
                                
                        except:
                            continue
                
                elapsed = time.time() - start_time
                print(f"✅ 收到完整回應 (耗時: {elapsed:.1f}秒, 區塊數: {chunk_count})")
                print(f"回應原始長度: {len(full_response)} 字元")
                
                if full_response:
                    # 直接返回原始回應
                    print(f"返回長度: {len(full_response)} 字元")
                    
                    # 檢查回應是否足夠詳細
                    if len(full_response) < 600:
                        print(f"⚠️ AI回應可能不夠詳細，添加補充說明")
                        full_response += "\n\n" + """
## 🔍 補充建議：

由於AI回應較為簡短，這裡提供一些額外建議：

### 📊 選擇策略：
1. **評分優先**：優先考慮4.5星以上的餐廳
2. **評價數量**：評價數越多越可靠
3. **近期評論**：查看最近一個月的評價
4. **照片驗證**：參考其他顧客的照片

### 🚗 交通提醒：
- 使用Google Maps規劃路線
- 確認停車資訊
- 考慮步行距離

### ⏰ 時間安排：
- 避開用餐高峰（11:30-13:00, 17:30-19:00）
- 熱門餐廳建議預約
- 確認營業時間是否有變動

### 💰 價格參考：
- 💰 (1/4)：平價，約150-250元
- 💰💰 (2/4)：中等，約250-400元  
- 💰💰💰 (3/4)：中高價，約400-600元
- 💰💰💰💰 (4/4)：高價，600元以上

祝您用餐愉快！ 🍽️"""
                    
                    return full_response
                else:
                    print("⚠️ 收到空回應")
                    return ChatAPIHandler._fallback_response(prompt)
            
            else:
                print(f"❌ API 錯誤: {response.status_code}")
                return ChatAPIHandler._fallback_response(prompt, error_code=response.status_code)
                
        except requests.exceptions.Timeout:
            print("⏰ 實驗室 API 回應超時")
            return ChatAPIHandler._fallback_response(prompt, timeout=True)
        except Exception as e:
            print(f"❌ 未預期錯誤: {e}")
            return ChatAPIHandler._fallback_response(prompt)
    
    @staticmethod
    def _fallback_response(prompt: str, **kwargs) -> str:
        """改進的備用回應"""
        if kwargs.get('timeout'):
            return """## ⏰ 回應超時

很抱歉，AI分析服務回應時間過長。

### 暫時建議：
1. 查看下方餐廳列表自行選擇
2. 使用 Google Maps 查看即時評價
3. 稍後再試 AI 分析功能

### 快速選擇指南：
- 優先選擇評分4.5星以上的餐廳
- 注意營業狀態（🟢營業中）
- 查看地址確認交通便利性"""
        
        error_code = kwargs.get('error_code')
        if error_code:
            return f"""## ❌ 服務暫時不可用 (錯誤碼: {error_code})

暫時無法提供 AI 分析，請參考下方的餐廳列表。

### 手動選擇建議：
1. **評分排序**：從高到低查看
2. **價格篩選**：根據預算選擇
3. **位置考量**：選擇步行可達的餐廳
4. **營業狀態**：優先選擇營業中的店家"""
        
        return """## 🍽️ 餐廳推薦指南

### 選擇策略
1. **評分優先**：4.5星以上餐廳品質較穩定
2. **評價數量**：評價數越多參考價值越高
3. **近期評論**：查看最近一個月的評價
4. **照片驗證**：參考其他顧客上傳的照片

### 價格參考
- 💰 (1/4)：平價，約150-250元
- 💰💰 (2/4)：中等，約250-400元
- 💰💰💰 (3/4)：中高價，約400-600元
- 💰💰💰💰 (4/4)：高價，600元以上

### 實用技巧
- **最佳時段**：平日11:00-12:30或17:00-18:30
- **預約建議**：週末或熱門餐廳建議預約
- **交通考量**：從火車站步行10分鐘內最佳
- **拍照時機**：上午自然光最適合拍照

*註：AI分析服務暫時不可用，此為基本選擇指南。*"""
    
    @staticmethod
    def test_connection() -> bool:
        """測試連接"""
        try:
            headers = {
                "Authorization": f"Bearer {LAB_API_TOKEN}",
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "model": LAB_MODEL,
                "prompt": "簡單測試，請回應'OK'",
                "stream": False,
                "max_tokens": 10
            }
            
            response = requests.post(
                LAB_OLLAMA_API,
                headers=headers,
                json=test_payload,
                timeout=10,
                verify=False
            )
            
            return response.status_code == 200
                
        except:
            return False

