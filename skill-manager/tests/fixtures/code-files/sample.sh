#!/bin/bash
install_deps() {
    npm install
    pip install -r requirements.txt
}

run_checks() {
    npm test && npm run lint
}