#!/bin/bash -xeu
#
# Local tests and linting.
# Build container.
# Push container.
#
cd """$(dirname "$0")""" || exit
cd ..

[[ ! -f ./VERSION.txt ]] && echo "Missing VERSION.txt" && exit 1

docker run -it ubuntu:latest /bin/bash -c 'echo "$(date +%Y.%m.%d)"' > ./VERSION.txt

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
time pytest --verbose --exitfirst || exit 1

time docker-compose build --compress --parallel --build-arg VERSION="$VERSION"