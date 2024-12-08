FROM python:3
RUN apt-get update -y && apt-get dist-upgrade -y
RUN useradd -ms /bin/bash tgbot
USER tgbot:tgbot
RUN mkdir /opt/sysadmin-tg-bot/
WORKDIR /opt/sysadmin-tg-bot/
RUN mkdir .venv && python3 -mvenv .venv && .venv/bin/pip install --update pip
COPY requirements.txt ./
COPY src ./
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt
CMD [".venv/bin/python3", "src/sysadmin_tg_bot.py"]