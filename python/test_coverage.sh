source ./venv/bin/activate

echo "Running tests"
coverage run --omit=./venv/*,./iot_app/test/* run_tests.py

coverage html -d coverage

echo "Done"
deactivate

