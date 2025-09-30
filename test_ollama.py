#!/usr/bin/env python3
"""
Test script to verify Ollama connection via ngrok
"""
import requests
import json

def test_ollama_connection():
    """Test connection to Ollama via ngrok"""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    
    # Try different model names that might be available
    model_names = ["llama3.1", "llama3", "llama2", "llama", "mistral"]

    for model_name in model_names:
        payload = {
            "model": model_name,
            "prompt": "Hello, how are you?",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 100
            }
        }
    
    headers = {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true"
    }

    for model_name in model_names:
        payload["model"] = model_name
        try:
            print(f"\nTesting Ollama connection with model: {model_name}")
            print(f"URL: {ollama_url}")
            print(f"Prompt: {payload['prompt']}")

            response = requests.post(
                ollama_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "").strip()
                print(f"✅ Success with {model_name}! Response: {generated_text}")
                return model_name  # Return the working model name
            else:
                print(f"❌ Failed with {model_name}: {response.status_code} - {response.text}")
                continue

        except requests.exceptions.Timeout:
            print(f"❌ Timeout with {model_name}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed with {model_name}: {e}")
            continue
        except Exception as e:
            print(f"❌ Unexpected error with {model_name}: {e}")
            continue

    print("❌ No working models found")
    return None

if __name__ == "__main__":
    working_model = test_ollama_connection()
    if working_model:
        print(f"\n✅ Ollama connection test passed with model: {working_model}")
    else:
        print("\n❌ Ollama connection test failed with all models!")
