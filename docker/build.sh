#!/bin/bash
VERSION=1.1.0
docker build --no-cache=true -t docker.psi.ch:5000/psen_processing .
docker tag docker.psi.ch:5000/psen_processing docker.psi.ch:5000/psen_processing:$VERSION
docker push docker.psi.ch:5000/psen_processing:$VERSION
docker push docker.psi.ch:5000/psen_processing
