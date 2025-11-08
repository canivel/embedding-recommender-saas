'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Book, Code, Copy, CheckCircle } from 'lucide-react';

export default function DocsPage() {
  const [activeSection, setActiveSection] = useState<'getting-started' | 'api-reference' | 'examples'>('getting-started');
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const copyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const pythonExample = `import requests

API_KEY = "your_api_key_here"
BASE_URL = "http://localhost:8000/api/v1"

# Get recommendations
response = requests.post(
    f"{BASE_URL}/recommendations",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "user_id": "user_123",
        "count": 10,
        "filters": {
            "categories": ["electronics"]
        }
    }
)

recommendations = response.json()
print(recommendations)`;

  const jsExample = `const API_KEY = 'your_api_key_here';
const BASE_URL = 'http://localhost:8000/api/v1';

async function getRecommendations(userId) {
  const response = await fetch(\`\${BASE_URL}/recommendations\`, {
    method: 'POST',
    headers: {
      'Authorization': \`Bearer \${API_KEY}\`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      user_id: userId,
      count: 10
    })
  });

  const data = await response.json();
  return data;
}

getRecommendations('user_123').then(console.log);`;

  const curlExample = `curl -X POST http://localhost:8000/api/v1/recommendations \\
  -H "Authorization: Bearer your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "user_123",
    "count": 10,
    "filters": {
      "categories": ["electronics"]
    }
  }'`;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Documentation</h1>
        <p className="text-gray-600 mt-1">
          Learn how to integrate and use the recommendation API
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <Card className="p-2">
            <nav className="space-y-1">
              <button
                onClick={() => setActiveSection('getting-started')}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeSection === 'getting-started'
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Book className="h-4 w-4" />
                Getting Started
              </button>
              <button
                onClick={() => setActiveSection('api-reference')}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeSection === 'api-reference'
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Code className="h-4 w-4" />
                API Reference
              </button>
              <button
                onClick={() => setActiveSection('examples')}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeSection === 'examples'
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Code className="h-4 w-4" />
                Code Examples
              </button>
            </nav>
          </Card>
        </div>

        {/* Content */}
        <div className="lg:col-span-3 space-y-6">
          {activeSection === 'getting-started' && (
            <>
              <Card>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  Getting Started
                </h2>
                <div className="prose max-w-none">
                  <h3 className="text-lg font-semibold text-gray-900 mt-6 mb-3">
                    1. Create an API Key
                  </h3>
                  <p className="text-gray-700">
                    Navigate to the API Keys page and create a new API key. Keep this
                    key secure as it won't be shown again.
                  </p>

                  <h3 className="text-lg font-semibold text-gray-900 mt-6 mb-3">
                    2. Upload Your Data
                  </h3>
                  <p className="text-gray-700">
                    Upload your product catalog using the Data Management page. Your CSV
                    should include columns: item_id, title, description, category.
                  </p>

                  <h3 className="text-lg font-semibold text-gray-900 mt-6 mb-3">
                    3. Make Your First Request
                  </h3>
                  <p className="text-gray-700">
                    Use your API key to make authenticated requests to the recommendation
                    endpoint. See the Code Examples section for sample code.
                  </p>
                </div>
              </Card>
            </>
          )}

          {activeSection === 'api-reference' && (
            <>
              <Card>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  API Endpoints
                </h2>

                <div className="space-y-6">
                  {/* Get Recommendations */}
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-mono font-semibold">
                        POST
                      </span>
                      <code className="text-sm font-mono">/api/v1/recommendations</code>
                    </div>
                    <p className="text-gray-700 text-sm mb-3">
                      Get personalized recommendations for a user
                    </p>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs font-semibold text-gray-700 mb-2">Request Body:</p>
                      <pre className="text-xs overflow-x-auto">
{`{
  "user_id": "string",
  "count": 10,
  "filters": {
    "categories": ["string"],
    "min_score": 0.5
  }
}`}
                      </pre>
                    </div>
                  </div>

                  {/* Upload Items */}
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-mono font-semibold">
                        POST
                      </span>
                      <code className="text-sm font-mono">/api/v1/items</code>
                    </div>
                    <p className="text-gray-700 text-sm mb-3">
                      Upload product items to the catalog
                    </p>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs font-semibold text-gray-700 mb-2">Request Body:</p>
                      <pre className="text-xs overflow-x-auto">
{`{
  "items": [
    {
      "item_id": "string",
      "title": "string",
      "description": "string",
      "category": "string",
      "tags": ["string"]
    }
  ]
}`}
                      </pre>
                    </div>
                  </div>

                  {/* Track Interaction */}
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-mono font-semibold">
                        POST
                      </span>
                      <code className="text-sm font-mono">/api/v1/interactions</code>
                    </div>
                    <p className="text-gray-700 text-sm mb-3">
                      Track user interactions with items
                    </p>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs font-semibold text-gray-700 mb-2">Request Body:</p>
                      <pre className="text-xs overflow-x-auto">
{`{
  "user_id": "string",
  "item_id": "string",
  "interaction_type": "view|click|purchase"
}`}
                      </pre>
                    </div>
                  </div>
                </div>
              </Card>
            </>
          )}

          {activeSection === 'examples' && (
            <>
              {/* Python Example */}
              <Card>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Python</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyCode(pythonExample, 'python')}
                  >
                    {copiedCode === 'python' ? (
                      <>
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4 mr-1" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                  {pythonExample}
                </pre>
              </Card>

              {/* JavaScript Example */}
              <Card>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">JavaScript</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyCode(jsExample, 'js')}
                  >
                    {copiedCode === 'js' ? (
                      <>
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4 mr-1" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                  {jsExample}
                </pre>
              </Card>

              {/* cURL Example */}
              <Card>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">cURL</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyCode(curlExample, 'curl')}
                  >
                    {copiedCode === 'curl' ? (
                      <>
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4 mr-1" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                  {curlExample}
                </pre>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
