from database.master_contract_db import download_master_contract
from utils.logging import get_logger

logger = get_logger(__name__)

print("🚀 Starting Master Contract download manually...")

try:
    success, message = download_master_contract()
    if success:
        print("✅ Master Contract download completed successfully:", message)
    else:
        print("❌ Master Contract download failed:", message)
except Exception as e:
    print("⚠️ Error during master contract download:", e)
