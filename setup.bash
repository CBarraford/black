#!/bin/bash

set -x
set -e

# create channel
chan=$(curl -sfH "Content-Type: application/json" -X POST -d '{"name": "general"}' "http://localhost:5001/channels/new" | jq -r .channel)

# Connect nodes
curl -fH "Content-Type: application/json" -X POST -d '{"remote_node": "http://node1:5000", "local_node": "http://node2:5000", "chan": "'"$chan"'"}' "http://localhost:5002/join"

# add a message to the general chat
curl -fH "Content-Type: application/json" -X POST -d '{
  "alias": "user1", 
  "pub_key": "-----BEGIN PUBLIC KEY-----\nMEkwEwYHKoZIzj0CAQYIKoZIzj0DAQEDMgAEUCXFlazfro8jch6LGcKaTd/HSZvC\nKT0aIPceW8JsOS5M82FMzkMRrtfuG5Kgi/Pa\n-----END PUBLIC KEY-----\n", 
  "signature": "8312DC578E8249E10877877066E82223BF31AD48207B51EB3389AF9D625FD503F2136297751E92657D18580BCCAFED3C",
  "message":"Hello World!"}
  ' "http://localhost:5001/$chan/transactions/new"
curl -fH "Content-Type: application/json" -X POST -d '{
  "alias": "user2", 
  "pub_key": "-----BEGIN PUBLIC KEY-----\nMEkwEwYHKoZIzj0CAQYIKoZIzj0DAQEDMgAEmKKhw/PJNmDMqtpNRXexw+l+sand\nBwVSdC0AgZ/Pj2O5e4a3SRvYRoIbYPOUC/Fq\n-----END PUBLIC KEY-----\n", 
  "signature": "E5FFF16FB17B5EBA0240D4083AEB8EDF90AA9610627DF015C2023233987A455F11BDB6959C7D872EDE4ED6B4F22E8C8A",
  "message":"Hello World also!"}
  ' "http://localhost:5002/$chan/transactions/new"

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
