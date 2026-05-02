FROM ubuntu
RUN apt-get update \
	&& apt-get install -y curl ca-certificates git xz-utils python3 python3-tornado python3-terminado \
	&& rm -rf /var/lib/apt/lists/*

# Install OpenClaw without performing onboarding at build time (avoid baking secrets)
ENV OPENCLAW_NO_PROMPT=1
RUN curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
RUN python3 --version

# Terminal UI server
COPY terminal_ui.py /opt/terminal_ui.py
EXPOSE 9090
CMD ["python3", "/opt/terminal_ui.py", "--host", "0.0.0.0", "--port", "9090"]