import hashlib
import sqlite3
import json
import time
from typing import Optional, Dict
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent
CACHE_DB = BASE_DIR / "cache.db"

# 快取系統
class QueryCache:
    def __init__(self):
        self.conn = sqlite3.connect(CACHE_DB, check_same_thread=False)
        self._init_db()
    
    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                query_hash TEXT PRIMARY KEY,
                question TEXT,
                location TEXT,
                response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def _generate_hash(self, question: str, location: str) -> str:
        return hashlib.md5(f"{question}|{location}".encode()).hexdigest()
    
    def get(self, question: str, location: str) -> Optional[Dict]:
        query_hash = self._generate_hash(question, location)
        
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT response FROM cache WHERE query_hash = ? AND expires_at > ?',
            (query_hash, datetime.now().isoformat())
        )
        
        result = cursor.fetchone()
        if result:
            try:
                cached_data = json.loads(result[0])
                print(f"📦 讀取快取成功 - recommendation長度: {len(cached_data.get('recommendation', '')) if 'recommendation' in cached_data else 0}")
                return cached_data
            except json.JSONDecodeError:
                return None
        
        return None
    
    def set(self, question: str, location: str, response: Dict):
        query_hash = self._generate_hash(question, location)
        expires_at = datetime.now() + timedelta(hours=24)
        
        # 檢查response結構
        print(f"💾 儲存快取 - recommendation存在: {'recommendation' in response}")
        if 'recommendation' in response:
            print(f"   recommendation長度: {len(response['recommendation'])}")
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO cache 
            (query_hash, question, location, response, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (query_hash, question, location, json.dumps(response), expires_at.isoformat()))
        self.conn.commit()