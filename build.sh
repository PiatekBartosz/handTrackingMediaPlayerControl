#!/usr/bin/env bash
set -e

echo "Budowanie paczki wheel..."
uv build

echo ""
echo "Gotowe! Paczka została zapisana w folderze dist/"
echo "Możesz ją zainstalować poleceniem:"
echo "    pip install dist/hand_tracking_media_player_control-*.whl"
