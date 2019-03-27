call iot_app\venv\Scripts\activate

echo Running tests
python -m coverage run run_tests.py

python -m coverage html -d coverage

echo Done
iot_app\venv\Scripts\deactivate

