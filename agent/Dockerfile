FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir psutil requests

COPY agent /app/agent

USER 1000:1000

ENTRYPOINT ["python", "-m", "agent.piops_agent.client"]
CMD ["--url", "http://127.0.0.1:8000", "--interval", "10"]
