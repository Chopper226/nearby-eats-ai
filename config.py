from dotenv import load_dotenv
import os

load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
LAB_API_TOKEN = os.getenv("LAB_API_TOKEN")

LAB_OLLAMA_API = "https://api-gateway.netdb.csie.ncku.edu.tw/api/generate"
LAB_MODEL = "gemma3:4b"
