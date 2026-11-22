#!/bin/bash
# three.js r147, the last release with classic (non-module) scripts: one file the page loads with a plain
# <script src>, so index.html opens from disk (file://) in Safari, Firefox and Chrome, offline.
set -e
B=https://cdn.jsdelivr.net/npm/three@0.147.0
cd "$(dirname "$0")/.."
for f in build/three.min.js examples/js/controls/OrbitControls.js examples/js/loaders/GLTFLoader.js \
         examples/js/environments/RoomEnvironment.js examples/js/utils/BufferGeometryUtils.js; do
  curl -sfL "$B/$f"; echo
done > three-r147.js
