#! /bin/bash -i
{{ python-executable }} -u "${APPDIR}/opt/python{{ python-version }}/bin/tbc-video-export" "$@"