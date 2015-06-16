#update setup.py with a new version
sudo pip install twine
sudo pip install wheel
python setup.py register
python setup.py sdist bdist_wheel upload

