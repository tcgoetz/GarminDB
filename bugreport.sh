#!/bin/bash

EPOCH=`date +'%s'`
BUGREPORT=bugreport.txt
PYTHON=python3
PYTHON_PACKAGES="sqlalchemy requests python-dateutil tqdm PyInstaller matplotlib"

zip -j -r bugreport_${EPOCH}.zip *.log

uname -a > ${BUGREPORT}
which ${PYTHON} >> ${BUGREPORT}
${PYTHON} --version >> ${BUGREPORT} 2>&1

echo "---" >> ${BUGREPORT}

echo Getting info for ${PYTHON_PACKAGES}
IFS=' '
read -ra PYTHON_PACKAGES_ARRAY <<< "$PYTHON_PACKAGES"
for package in "${PYTHON_PACKAGES_ARRAY[@]}"; do \
    echo getting info for ${package}; \
    pip show ${package} >> ${BUGREPORT}; \
    echo "---" >> ${BUGREPORT}; \
done

if [ -f garmindb_cli.py ]; then
    echo Getting GarminDB version
    echo --- >> ${BUGREPORT}
    echo -n "GarminDB version " >> ${BUGREPORT}
    ${PYTHON} garmindb_cli.py --version >> ${BUGREPORT}
fi

echo Zipping up ${BUGREPORT} and logs
zip -j -r bugreport_${EPOCH}.zip ${BUGREPORT}
