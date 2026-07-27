import os
from dotenv import load_dotenv
from supabase import create_client

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_ANON_KEY")

if not url or not key:
    print("Missing credentials")
    exit(1)

supabase = create_client(url, key)

agents = [
    {"agent_name": "Транскрибатор", "status": "IDLE", "active_task": ""},
    {"agent_name": "Аудитор", "status": "IDLE", "active_task": ""},
    {"agent_name": "QA аналитик", "status": "IDLE", "active_task": ""}
]

for agent in agents:
    try:
        # We need to make sure the row is upserted. Since agent_name is unique, we upsert on it.
        # But wait, in supabase-py, upserting requires specifying the conflict columns.
        res = supabase.table("agent_telemetry").upsert(agent, on_conflict="agent_name").execute()
        print(f"Upserted {agent['agent_name']}: {res.data}")
    except Exception as e:
        print(f"Failed to upsert {agent['agent_name']}: {e}")
