#!/bin/sh
cd /monorepo/uis/website && npm run dev -- -p 3000 -H 0.0.0.0 &
cd /monorepo/uis/backoffice && npm run dev -- -p 3001 -H 0.0.0.0 &
wait
