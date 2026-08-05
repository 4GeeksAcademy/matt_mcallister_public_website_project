FROM python:3.11-slim

WORKDIR /app

COPY mcps/company_tools/requirements.txt /tmp/mcp-requirements.txt
RUN pip install --no-cache-dir -r /tmp/mcp-requirements.txt

COPY mcps /app/mcps

ENV PYTHONPATH=/app
ENV MCP_SERVER_HOST=0.0.0.0
ENV MCP_SERVER_PORT=8006

EXPOSE 8006

CMD ["uvicorn", "mcps.company_tools.server:app", "--host", "0.0.0.0", "--port", "8006"]
