FROM python:3.11

ENV PYTHONBUFFERED = 1


COPY src/requirements.txt src/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r src/requirements.txt

COPY src /src

#ENV DATABASE twitter-clone_db
#ENV DATABASE_USER twitter-clone
#ENV DATABASE_PASSWORD secret
#ENV DATABASE_PORT 5432
#ENV DEBUG 0
#ENV API_ROUTE /api

#CMD ["python", "src/settings.py"]

ENTRYPOINT ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

#/static/images/2#
