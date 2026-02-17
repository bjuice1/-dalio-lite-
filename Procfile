web: streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0
autopilot: python -c "from dalio_lite import DalioLite; import time; dalio = DalioLite(); [dalio.run_daily_check() or time.sleep(86400) for _ in iter(int, 1)]"
