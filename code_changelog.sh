#!/bin/bash

lines=$(git diff $DRONE_TARGET_BRANCH..$DRONE_SOURCE_BRANCH -- CHANGELOG.md --unified=0| wc -l)
echo "$lines lines modified on CHANGELOG.md in PR $DRONE_SOURCE_BRANCH -> $DRONE_TARGET_BRANCH"

if [[ -n "$lines" ]]
  then
  echo -e "\nCHANGELOG.md has not been updated. Update it for the PR to be accepted in CI.\n"
  exit 1
fi


