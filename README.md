# iOVU-AI

가상환경 python env
python -m venv iovu-env

가상환경 실행 후 (pip update 하는게 좋음)
pip install fastapi uvicorn

Fast Api 실행
uvicorn main:app --reload
http://127.0.0.1:8000/ (default)
