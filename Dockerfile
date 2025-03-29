FROM python:3
RUN apt-get update -y && apt-get dist-upgrade -y && apt-get install -y whois bind9-host
RUN useradd -ms /bin/bash tgbot
RUN mkdir -m ug=rwx,o-rwx /opt/sysadmin-tg-bot/ && chown tgbot:tgbot /opt/sysadmin-tg-bot
WORKDIR /opt/sysadmin-tg-bot/
USER tgbot:tgbot
RUN mkdir .venv && python3 -mvenv .venv && .venv/bin/pip install --upgrade pip
COPY requirements.txt src sysadmin-tg-bot.yaml ./
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt
ENTRYPOINT [".venv/bin/python3", "sysadmin_tg_bot.py"]