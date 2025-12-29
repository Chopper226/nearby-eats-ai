import uvicorn

from app import app

if __name__ == "__main__":
    print("""
    🚀 附近吃吃推薦！
    
    服務資訊：
    - API 地址：http://localhost:5525
    - API 文件：http://localhost:5525/docs

    
    測試連接：
    curl http://localhost:5525/api/health
    curl http://localhost:5525/api/test_ai
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5525,
        log_level="info"
    )