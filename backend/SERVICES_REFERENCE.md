# Quick Reference: Supported API Key Services

## 🧠 LLM Providers (4)
| Service | Key | Category |
|---------|-----|----------|
| Anthropic (Claude) | `anthropic` | LLM |
| OpenAI (GPT) | `openai` | LLM |
| Together AI | `together_ai_token` | LLM |
| Cohere | `cohere_token` | LLM |

## 🤗 AI/ML Platforms (2)
| Service | Key | Category |
|---------|-----|----------|
| Hugging Face | `huggingface_token` | AI/ML |
| Replicate | `replicate_token` | AI/ML |

## ☁️ Cloud Providers (3)
| Service | Key | Category |
|---------|-----|----------|
| AWS | `aws_key` | Cloud |
| GCP | `gcp_key` | Cloud |
| Azure | `azure_key` | Cloud |

## 🔧 Developer Tools (3)
| Service | Key | Category |
|---------|-----|----------|
| GitHub | `github_token` | Development |
| Google (Drive/Sheets/Docs) | `google_token` | Productivity |
| Databricks | `databricks_token` | Data |

## 💬 Communication (4)
| Service | Key | Category |
|---------|-----|----------|
| Slack | `slack_token` | Communication |
| Discord | `discord_token` | Communication |
| Twilio | `twilio_key` | Communication |
| SendGrid | `sendgrid_key` | Communication |

## 💳 Financial (1)
| Service | Key | Category |
|---------|-----|----------|
| Stripe | `stripe_key` | Financial |

## 🔑 Custom (1)
| Service | Key | Category |
|---------|-----|----------|
| Custom API Key | `custom_api_key` | Other |

---

## Usage Example

### Adding via Frontend
1. Settings → API Keys Management
2. Select "Anthropic (Claude)" from dropdown
3. Paste your key: `sk-ant-...`
4. Click "Add API Key"

### Adding via API
```bash
curl -X POST http://localhost:8000/api/settings/keys/anthropic \
  -H "Content-Type: application/json" \
  -d '{"key":"sk-ant-..."}' \
  -G -d "user_id=default"
```

### Listing Keys
```bash
curl http://localhost:8000/api/settings/keys?user_id=default
```

Response:
```json
{
  "keys": {
    "anthropic": true,
    "openai": false,
    "github_token": true
  }
}
```

### Deleting a Key
```bash
curl -X DELETE http://localhost:8000/api/settings/keys/anthropic?user_id=default
```

## Total: 18 Service Types

✅ Unlimited keys per service (overwrites previous)
✅ All encrypted with Fernet cipher
✅ Organized by category
✅ Easy management in UI
✅ RESTful API for programmatic access
