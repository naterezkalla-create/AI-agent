#!/bin/bash

# Register test user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "naterezkalla@gmail.com",
    "password": "Converse14",
    "full_name": "Nate"
  }' | jq .
