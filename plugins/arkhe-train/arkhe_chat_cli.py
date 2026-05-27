#!/usr/bin/env python3

import sys
import json
import requests

def chat_local():
    """Interacts with the local llama.cpp server running ARKHE-OS."""
    print("ARKHE CHAT - Local Interaction with ARKHE-OS")
    print("Type 'exit' or 'quit' to stop.")

    server_url = "http://localhost:8080/completion"

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                break

            payload = {
                "prompt": user_input,
                "n_predict": 128
            }

            response = requests.post(server_url, json=payload)
            if response.status_code == 200:
                data = response.json()
                print(f"ARKHE-OS: {data.get('content', '')}")
            else:
                print(f"Error communicating with server: {response.status_code}")

        except KeyboardInterrupt:
            break
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}. Is the Docker server running?")

if __name__ == "__main__":
    chat_local()
