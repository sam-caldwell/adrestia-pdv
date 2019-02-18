#!/bin/bash -eu
#
# Local tests and linting.
# Build container.
# Push container.
#
cd """$(dirname "$0")""" || exit
cd ..

[[ ! -f ./VERSION.txt ]] && echo "Missing VERSION.txt" && exit 1

pip install --upgrade pip

docker run -it ubuntu:latest /bin/bash -c 'echo -n "$(date +%Y.%m.%d)"' > ./VERSION.txt

export VERSION="$(cat ./VERSION.txt)"

[[ "$VERSION" == "" ]] && echo "empty version" && exit 1

echo "building $VERSION"

(
    git add VERSION.txt && \
    git commit -m "Updating version to $VERSION" && \
    git push origin master || true
) || true

[[ -d ./venv ]] && {
    source ./venv/bin/activate
}
time pip install -r requirements.txt

time flake8 --exclude venv/ --doctests --count --jobs=10 || exit 1
time pytest --verbose --exitfirst --disable-warnings || exit 1

container_image_name="adrestia-pdv:$VERSION"
docker build --tag "$container_image_name" --squash --compress ./
echo "Created adrestia-pdv:$VERSION"

docker images | grep pdv

echo "Tagging for latest"
docker tag adrestia-pdv:$VERSION adrestia-pdv:latest

docker push $container_image_name x684867/adrestia-pdv:$VERSION
docker push $container_image_name x684867/adrestia-pdv:latest

docker images | grep pdv