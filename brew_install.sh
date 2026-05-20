#!/bin/bash
export NONINTERACTIVE=1
echo "1234" | sudo -S -v
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
