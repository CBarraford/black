#!/bin/bash

set -x
set -e

# create channel
chan=$(curl -sfH "Content-Type: application/json" -X POST -d '{"name": "general"}' "http://localhost:5001/channels/new" | jq -r .channel)

# Connect nodes
curl -fH "Content-Type: application/json" -X POST -d '{"remote_node": "http://node1:5000", "local_node": "http://node2:5000", "chan": "'"$chan"'"}' "http://localhost:5002/join"

# add a message to the general chat
curl -fH "Content-Type: application/json" -X POST -d '{"sender": "user1", "message":"Hello World!"}' "http://localhost:5001/$chan/transactions/new"
curl -fH "Content-Type: application/json" -X POST -d '{"sender": "user2", "message":"Hello World also!"}' "http://localhost:5002/$chan/transactions/new"

# mine it
curl -f "http://localhost:5001/$chan/mine"

# resolve
curl -f "http://localhost:5001/$chan/nodes/resolve"
curl -f "http://localhost:5002/$chan/nodes/resolve"

# check chains
curl -f "http://localhost:5001/$chan/chain"
curl -f "http://localhost:5002/$chan/chain"

# mine the second node
curl -f "http://localhost:5002/$chan/mine"

# resolve
curl -f "http://localhost:5001/$chan/nodes/resolve"
curl -f "http://localhost:5002/$chan/nodes/resolve"

# check chains
curl -f "http://localhost:5001/$chan/chain"
curl -f "http://localhost:5002/$chan/chain"
