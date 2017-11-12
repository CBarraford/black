#!/bin/bash

# Connect nodes
curl -H "Content-Type: application/json" -X POST -d '{"nodes":["http://node2:5000"]}' "http://localhost:5001/nodes/register"
curl -H "Content-Type: application/json" -X POST -d '{"nodes":["http://node1:5000"]}' "http://localhost:5002/nodes/register"

# add a message to the general chat
curl -H "Content-Type: application/json" -X POST -d '{"sender": "user1", "message":"Hello World!"}' "http://localhost:5001/transactions/new"
curl -H "Content-Type: application/json" -X POST -d '{"sender": "user2", "message":"Hello World also!"}' "http://localhost:5002/transactions/new"

# mine it
curl "http://localhost:5001/mine"

# resolve
curl "http://localhost:5001/nodes/resolve"
curl "http://localhost:5002/nodes/resolve"

# check chains
curl "http://localhost:5001/chain"
curl "http://localhost:5002/chain"
