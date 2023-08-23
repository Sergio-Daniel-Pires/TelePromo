from python:3.10-slim

# Env dependencies
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright

# Install & use pipenv
COPY Pipfile Pipfile.lock ./
RUN python -m pip install --upgrade pip
RUN pip install pipenv && pipenv install --dev --system --deploy

# Install sklearn
# RUN apt-get install python-sklearn
RUN apt-get update
RUN apt-get -y install fontconfig
# COPY /fonts ~/.fonts
# COPY /fonts /usr/shared/fonts
# COPY /fonts /usr/share/fonts/truetype
# refresh system font cache
RUN fc-cache -f -v

# Install playwright deps
RUN apt-get update
RUN apt-get install -y gconf-service libasound2 libatk1.0-0 libcairo2 libcups2 libfontconfig1 libgdk-pixbuf2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libxss1 fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils
RUN PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright python -m playwright install --with-deps chromium

WORKDIR /telepromo