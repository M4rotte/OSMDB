#!/bin/sh
# Build osmdb as a single executable using PyInstaller
SCRIPT_NAME='osmdb'

pyinstaller -p src --strip --log-level DEBUG -y --clean -F "$SCRIPT_NAME"
echo
du -sh "dist/$SCRIPT_NAME"
echo
ldd "dist/$SCRIPT_NAME"
echo

exit 0

