Terminal 1 — Hadoop + Hive
Start Hadoop:
start-all.sh
mapred --daemon start historyserver
Start HiveServer2:
export HIVE_AUX_JARS_PATH=$HOME/hive/lib/commons-collections-3.2.2.jar
hiveserver2 &
Wait a few seconds for HiveServer2 to start.

Terminal 2 — FastAPI Backend
cd /mnt/c/Vault/Projects/food_delivery_analysis/backend
source .venv/bin/activate
python main.py
The backend loads dashboard_cache.json and runs on port 8000.

Terminal 3 — Frontend
Open Windows PowerShell:
cd C:\Vault\Projects\food_delivery_analysis\frontend
npm run dev
Open:
http://localhost:5173