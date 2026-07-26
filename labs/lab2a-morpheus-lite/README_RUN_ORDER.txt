MORPHEUS LITE LABORATORY v1.0 - RUN ORDER

Use one terminal per service.

1. START REDPANDA AND CONSOLE
   docker compose up -d redpanda console

2. START TELEMETRY
   python telemetry_generator.py

3. START DETECTOR
   python morpheus_lite_detector.py

4. START AGENT ORCHESTRATOR
   python agent_orchestrator.py

5. START DASHBOARD
   streamlit run dashboard.py

Open:
   Dashboard:         http://localhost:8501
   Redpanda Console:  http://localhost:8080

Dashboard procedure:
   - Click Fetch new cases from Kafka.
   - In All Cases, use the first-column Select checkbox.
   - Verify that Active alert, Human Decision Queue, and Case Details show the same alert_id.
   - Review evidence, RAI, XAI, and Meta-AI.
   - Record a human decision and justification.

Research export:
   python export_research_data.py

Shutdown:
   Stop Python services with Ctrl+C.
   docker compose down
