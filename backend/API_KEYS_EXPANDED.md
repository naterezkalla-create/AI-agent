# API Keys - Expanded Services Support

## Now Supporting 18+ Services

Your system now supports adding API keys for numerous services across multiple categories:

### 🧠 LLM Providers
- **Anthropic (Claude)** - Most advanced reasoning
- **OpenAI (GPT-4, GPT-3.5)** - Latest GPT models
- **Together AI** - Fast inference
- **Cohere** - Text generation

### 🤗 AI/ML Platforms
- **Hugging Face** - 500k+ models
- **Replicate** - Reproducible ML

### ☁️ Cloud Providers
- **AWS** - Comprehensive cloud services
- **GCP** - Google Cloud Platform
- **Azure** - Microsoft cloud

### 🔧 Developer Tools
- **GitHub** - Repositories and Gists
- **Google** - Drive, Sheets, Docs
- **Databricks** - Data analytics

### 💬 Communication
- **Slack** - Team messaging
- **Discord** - Community chat
- **Twilio** - SMS/Voice
- **SendGrid** - Email delivery

### 💳 Financial
- **Stripe** - Payment processing

### 🔑 Custom
- **Custom API Key** - Any other service

## Features

✅ **Unlimited Keys** - Add as many API keys as needed
✅ **Category Organization** - Services grouped by type
✅ **Grouped Dropdown** - Easy service selection
✅ **Visual Summary** - See all configured services at a glance
✅ **Individual Delete** - Remove keys one at a time
✅ **Quick Add** - Press Enter to submit
✅ **Security** - Each key encrypted individually with Fernet

## Usage

1. Go to **Settings** → **API Keys Management**
2. Select a service from the organized dropdown
3. Paste your API key
4. Click **Add API Key** or press Enter
5. See your key appear in the "Configured Services" list
6. Delete any key by clicking the X button

## Security

- Each key is encrypted with Fernet cipher before storage
- Keys are only decrypted when the agent uses them
- Database stores only encrypted values
- No keys appear in logs or API responses
- Your encryption key is secured in `.env`

## Adding More Services

To add new services:

**Backend** (`app/api/settings.py`):
```python
valid_services = [
    # ... existing services ...
    "new_service_key",
]
```

**Frontend** (`frontend/src/pages/SettingsPage.tsx`):
```javascript
const availableServices = [
  // ... existing services ...
  { id: 'new_service_key', label: 'Service Name', category: 'Category' },
];
```

## API Endpoints

- `GET /api/settings/keys` - List configured services
- `POST /api/settings/keys/{service}` - Add encrypted key
- `DELETE /api/settings/keys/{service}` - Remove key

Example:
```bash
# Add OpenAI key
curl -X POST http://localhost:8000/api/settings/keys/openai \
  -H "Content-Type: application/json" \
  -d '{"key": "sk-..."}' \
  -G -d "user_id=default"
```

## Notes

- Keys are unique per user (using user_id from settings)
- Same service can only have one key per user
- Adding a new key for a service overwrites the old one
- Use minimal permission keys when possible
- Rotate keys regularly for security
