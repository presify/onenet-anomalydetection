FROM python:3.10
WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN pip install "uvicorn[standard]"

CMD [ "python3", "./main.py" ]
