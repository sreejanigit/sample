module_path=src/modulefactory
# package the modules
echo "Install the dependencies"
pip3 install -r $module_path/requirements.txt -t $module_path --no-cache-dir