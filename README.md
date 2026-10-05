# Food Delivery Demand Analysis and Delivery Optimization Using Hadoop and Hive

A simple Big Data Analytics project using Hadoop 3.4.2, HDFS, YARN, MapReduce, Hive 4.1.0, FastAPI, React + Vite, and Recharts.

## Architecture

```text
train.csv
    |
    v
  HDFS
    |
    v
  Hive
    |
    v
MapReduce
    |
    v
FastAPI
    |
    v
In-memory cache
    |
    v
React Dashboard
```

Hive/MapReduce performs the expensive analytics. FastAPI caches the results, and React reads the cached dashboard data.

---

# 1. Project Location

Windows:

```text
C:\Vault\Projects\food_delivery_analysis
```

WSL:

```text
/mnt/c/Vault/Projects/food_delivery_analysis
```

Expected structure:

```text
food_delivery_analysis/
├── backend/
│   ├── backend.py
│   └── .venv/
├── frontend/
│   ├── package.json
│   └── src/
├── train.csv
└── README.md
```

---

# 2. Open Ubuntu / WSL

Open Ubuntu from Windows.

Check:

```bash
ls
```

The installations should be:

```text
~/hadoop
~/hive
```

---

# 3. Set Environment Variables

Run this in every new Ubuntu terminal unless you add them permanently to `~/.bashrc`:

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

export HADOOP_HOME=$HOME/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop

export HIVE_HOME=$HOME/hive

export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$HIVE_HOME/bin

export HIVE_AUX_JARS_PATH=$HIVE_HOME/lib/commons-collections-3.2.2.jar
```

Verify:

```bash
java -version
hadoop version
hive --version
```

Expected major versions:

```text
Java 17
Hadoop 3.4.2
Hive 4.1.0
```

---

# 4. Start Hadoop

Start HDFS:

```bash
start-dfs.sh
```

Start YARN:

```bash
start-yarn.sh
```

Start the MapReduce JobHistory Server:

```bash
mapred --daemon start historyserver
```

Check:

```bash
jps
```

You should see approximately:

```text
NameNode
DataNode
SecondaryNameNode
ResourceManager
NodeManager
JobHistoryServer
Jps
```

---

# 5. Verify HDFS

```bash
hdfs dfs -ls /
```

Check the raw dataset:

```bash
hdfs dfs -ls /food_delivery/raw
```

Expected:

```text
train.csv
```

Check the Hive table data:

```bash
hdfs dfs -ls /user/hive/warehouse/food_delivery.db/deliveries
```

---

# 6. Start HiveServer2

IMPORTANT: set the auxiliary JAR before starting HiveServer2:

```bash
export HIVE_AUX_JARS_PATH=$HIVE_HOME/lib/commons-collections-3.2.2.jar
```

Start:

```bash
hiveserver2 &
```

Wait a few seconds.

Check:

```bash
jps
```

A HiveServer2 Java process should appear as a `RunJar` process.

---

# 7. Test Hive

Connect:

```bash
beeline -u 'jdbc:hive2://localhost:10000/default'
```

Then:

```sql
SHOW DATABASES;
```

You should see:

```text
food_delivery
```

Select the database:

```sql
USE food_delivery;
```

Check the table:

```sql
SHOW TABLES;
```

Expected:

```text
deliveries
```

Check the number of records:

```sql
SELECT COUNT(*) FROM deliveries;
```

Expected:

```text
45594
```

Test a real Hive/MapReduce aggregation:

```sql
SELECT city, COUNT(*) AS total_orders
FROM deliveries
GROUP BY city
ORDER BY total_orders DESC;
```

Expected approximately:

```text
Metropolitian    34093
Urban            10136
NaN               1200
Semi-Urban         164
City                 1
```

The application filters invalid `NaN` and header-like `City` values where appropriate.

Exit:

```sql
!quit
```

---

# 8. Start the FastAPI Backend

The backend must run inside WSL because it calls WSL's `beeline`.

Go to the backend:

```bash
cd /mnt/c/Vault/Projects/food_delivery_analysis/backend
```

Activate the Python environment:

```bash
source .venv/bin/activate
```

Set the required environment:

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

export HADOOP_HOME=$HOME/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop

export HIVE_HOME=$HOME/hive

export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$HIVE_HOME/bin

export HIVE_AUX_JARS_PATH=$HIVE_HOME/lib/commons-collections-3.2.2.jar
```

Start:

```bash
python backend.py
```

Expected:

```text
Uvicorn running on http://0.0.0.0:8000
```

The backend should automatically run the dashboard Hive queries and populate its in-memory cache.

You should see logs similar to:

```text
[HIVE] Starting dashboard analysis...

[HIVE] summary SUCCESS
[HIVE] orders-by-city SUCCESS
[HIVE] orders-by-traffic SUCCESS
[HIVE] orders-by-weather SUCCESS
[HIVE] orders-by-vehicle SUCCESS
[HIVE] orders-by-festival SUCCESS
[HIVE] distance-by-city SUCCESS
[HIVE] filters SUCCESS

[HIVE] Dashboard cache loaded
[HIVE] Successful: 8/8
```

Each query may take around 20–30 seconds on the single-node setup.

---

# 9. Test FastAPI

Open:

```text
http://localhost:8000
```

Health:

```text
http://localhost:8000/api/health
```

Dashboard cache:

```text
http://localhost:8000/api/dashboard
```

Cache status:

```text
http://localhost:8000/api/cache-status
```

The important dashboard endpoint is:

```text
GET /api/dashboard
```

It should return all cached analytical results in one response.

---

# 10. Start the React Frontend

Open another Ubuntu terminal.

Go to:

```bash
cd /mnt/c/Vault/Projects/food_delivery_analysis/frontend
```

Install dependencies if this is the first run:

```bash
npm install
```

Start Vite:

```bash
npm run dev
```

You should see something similar to:

```text
Local: http://localhost:5173/
```

Open:

```text
http://localhost:5173
```

---

# 11. Normal Startup Order

After restarting the computer or closing all Ubuntu terminals:

## Terminal 1 — Hadoop

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export HADOOP_HOME=$HOME/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HIVE_HOME=$HOME/hive
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$HIVE_HOME/bin
export HIVE_AUX_JARS_PATH=$HIVE_HOME/lib/commons-collections-3.2.2.jar

start-dfs.sh
start-yarn.sh
mapred --daemon start historyserver
```

Check:

```bash
jps
```

## Terminal 2 — HiveServer2

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export HADOOP_HOME=$HOME/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HIVE_HOME=$HOME/hive
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$HIVE_HOME/bin
export HIVE_AUX_JARS_PATH=$HIVE_HOME/lib/commons-collections-3.2.2.jar

hiveserver2 &
```

## Terminal 3 — Backend

```bash
cd /mnt/c/Vault/Projects/food_delivery_analysis/backend
source .venv/bin/activate

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export HADOOP_HOME=$HOME/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HIVE_HOME=$HOME/hive
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$HIVE_HOME/bin
export HIVE_AUX_JARS_PATH=$HIVE_HOME/lib/commons-collections-3.2.2.jar

python backend.py
```

Wait for the Hive analysis/cache to finish.

## Terminal 4 — Frontend

```bash
cd /mnt/c/Vault/Projects/food_delivery_analysis/frontend
npm run dev
```

Open:

```text
http://localhost:5173
```

---

# 12. If You Open a New Ubuntu Tab

Environment variables are normally per-terminal.

Run:

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export HADOOP_HOME=$HOME/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HIVE_HOME=$HOME/hive
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$HIVE_HOME/bin
export HIVE_AUX_JARS_PATH=$HIVE_HOME/lib/commons-collections-3.2.2.jar
```

To make them permanent:

```bash
nano ~/.bashrc
```

Add:

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export HADOOP_HOME=$HOME/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HIVE_HOME=$HOME/hive
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$HIVE_HOME/bin
export HIVE_AUX_JARS_PATH=$HIVE_HOME/lib/commons-collections-3.2.2.jar
```

Save, then:

```bash
source ~/.bashrc
```

---

# 13. If Hadoop Is Already Running

Check:

```bash
jps
```

If you already see:

```text
NameNode
DataNode
SecondaryNameNode
ResourceManager
NodeManager
JobHistoryServer
```

do not start them again.

Only start whatever is missing.

---

# 14. If HiveServer2 Is Already Running

Test:

```bash
beeline -u 'jdbc:hive2://localhost:10000/default'
```

If Beeline connects, HiveServer2 is already running.

Do not start another HiveServer2 unnecessarily.

---

# 15. If You Get the Commons Collections Error

If Hive reports:

```text
NoClassDefFoundError:
org/apache/commons/collections/CollectionUtils
```

run:

```bash
export HIVE_AUX_JARS_PATH=$HOME/hive/lib/commons-collections-3.2.2.jar
```

Then restart HiveServer2.

---

# 16. If Backend Says `beeline` Was Not Found

Check:

```bash
echo $HIVE_HOME
```

Expected:

```text
/home/atulr/hive
```

Then:

```bash
which beeline
```

Expected something similar to:

```text
/home/atulr/hive/bin/beeline
```

If not:

```bash
export HIVE_HOME=$HOME/hive
export PATH=$PATH:$HIVE_HOME/bin
```

Test:

```bash
beeline --version
```

---

# 17. If FastAPI Says `ModuleNotFoundError`

Go to:

```bash
cd /mnt/c/Vault/Projects/food_delivery_analysis/backend
```

Activate:

```bash
source .venv/bin/activate
```

Check:

```bash
which python
```

It should point to the backend `.venv`.

If required:

```bash
pip install fastapi uvicorn
```

Then:

```bash
python backend.py
```

---

# 18. If the Frontend Shows "Loading"

Check:

```text
http://localhost:8000/api/cache-status
```

If:

```json
{
  "ready": false
}
```

the Hive analysis is still running.

Wait until:

```json
{
  "ready": true
}
```

Then refresh the frontend.

If the backend is unavailable, start it using the backend instructions above.

---

# 19. If Hive Queries Are Slow

This is expected on the current single-node Hadoop setup.

The important architecture is:

```text
Hive/MapReduce
      |
      | 20–30 sec
      v
FastAPI cache
      |
      | fast
      v
React dashboard
```

The frontend should not start a new Hive MapReduce job for every chart.

---

# 20. Refreshing the Dashboard

The frontend has a:

```text
Refresh Analysis
```

button.

It calls:

```text
POST /api/refresh
```

This intentionally reruns the Hive analysis and rebuilds the cache.

---

# 21. Dataset Information

Dataset:

```text
train.csv
```

Records:

```text
45,594
```

The original `Time_taken(min)` column was removed.

The Hive table contains 19 columns.

Hive database:

```text
food_delivery
```

Hive table:

```text
deliveries
```

Raw HDFS dataset:

```text
/food_delivery/raw/train.csv
```

Hive warehouse:

```text
/user/hive/warehouse/food_delivery.db/deliveries
```

---

# 22. Quick Health Check

If something is not working, check these in order.

### Java

```bash
java -version
```

### Hadoop processes

```bash
jps
```

### HDFS

```bash
hdfs dfs -ls /
```

### YARN

```bash
yarn node -list
```

### Hive

```bash
beeline -u 'jdbc:hive2://localhost:10000/default'
```

### Hive data

Inside Beeline:

```sql
USE food_delivery;
SHOW TABLES;
SELECT COUNT(*) FROM deliveries;
```

### FastAPI

Open:

```text
http://localhost:8000/api/health
```

### Cache

Open:

```text
http://localhost:8000/api/cache-status
```

### React

Open:

```text
http://localhost:5173
```

---

# 23. Complete Startup Cheat Sheet

Once the environment variables are permanent, the basic commands are:

### Terminal 1

```bash
start-dfs.sh
start-yarn.sh
mapred --daemon start historyserver
```

### Terminal 2

```bash
export HIVE_AUX_JARS_PATH=$HOME/hive/lib/commons-collections-3.2.2.jar
hiveserver2 &
```

### Terminal 3

```bash
cd /mnt/c/Vault/Projects/food_delivery_analysis/backend
source .venv/bin/activate
export HIVE_AUX_JARS_PATH=$HOME/hive/lib/commons-collections-3.2.2.jar
python backend.py
```

### Terminal 4

```bash
cd /mnt/c/Vault/Projects/food_delivery_analysis/frontend
npm run dev
```

Then:

```text
http://localhost:5173
```

---

# 24. Final Project Flow

For the project demonstration:

```text
Dataset
   ↓
HDFS stores raw dataset
   ↓
Hive creates/manages deliveries table
   ↓
Hive executes analytical SQL
   ↓
Hive uses MapReduce for aggregation
   ↓
FastAPI executes Hive analysis
   ↓
FastAPI caches processed results
   ↓
React fetches cached results
   ↓
Dashboard displays food delivery insights
```

This keeps the implementation simple while genuinely demonstrating Hadoop + HDFS + YARN + MapReduce + Hive.
#   f o o d - d e l i v e r y - a n a l y s i s  
 