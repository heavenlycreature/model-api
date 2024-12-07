FROM python:3.9-slim

WORKDIR /src

COPY . .

RUN mkdir -p /app/tmp && pip install --no-cache-dir --build /app/tmp -r requirements.txt


CMD [ "python", "api.py" ]

EXPOSE 5000

