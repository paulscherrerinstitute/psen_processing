#!/bin/bash
VERSION=1.2.2

docker build --no-cache=true -t paulscherrerinstitute/psen_processing .
docker tag paulscherrerinstitute/psen_processing paulscherrerinstitute/psen_processing:$VERSION
docker login
docker push paulscherrerinstitute/psen_processing:$VERSION
docker push paulscherrerinstitute/psen_processing
