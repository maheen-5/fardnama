#!/bin/sh
set -eu

printf '%s\n' 'Applying private IPFS configuration...'

if ipfs bootstrap rm --all >/dev/null 2>&1; then
  printf '%s\n' 'Removed all bootstrap peers.'
else
  printf '%s\n' 'No bootstrap peers to remove.'
fi

if ipfs config --json Routing '{"Type":"none"}'; then
  printf '%s\n' 'Set Routing.Type to "none".'
else
  printf '%s\n' 'Routing.Type update failed.' >&2
  exit 1
fi

if ipfs config --json Discovery '{"MDNS":{"Enabled":false}}'; then
  printf '%s\n' 'Set Discovery.MDNS.Enabled to false.'
else
  printf '%s\n' 'Discovery.MDNS.Enabled update failed.' >&2
  exit 1
fi

printf '%s\n' 'Private IPFS init complete.'
