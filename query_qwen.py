#!/usr/bin/env python3
import requests
import json

def query_qwen(question):
    """Query the QWen model running in Docker Ollama"""
    
    # API endpoint
    url = "http://192.168.123.240:8034/api/generate"
    
    # Request payload
    payload = {
        "model": "qwen2.5:7b-instruct-q8_0",
        "prompt": question,
        "stream": False
    }
    
    # Headers
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API call
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the response
        result = response.json()
        
        # Display the result
        print(f"Question: {question}\n")
        print(f"Answer: {result['response']}")
        
        return result['response']
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return None

if __name__ == "__main__":
    # Set your question here
    question = "What are the best practices for error handling in JavaScript?"
    
    # Query the model
    query_qwen(question)
