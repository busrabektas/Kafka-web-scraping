# use base image as Pythın 3.8-slim
FROM python:3.8-slim

#set the workin directory inside the container
WORKDIR /app

# copy all files from the current directory to the working directory in the container
COPY . .

#install dependcies 
RUN pip install -r requirements.txt

# Specify the commands to run when the container
CMD ["python", "scraper.py"]

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]


