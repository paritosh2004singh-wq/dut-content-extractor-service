import base64
import os
import json
from mistralai.client import Mistral

def main():
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("MISTRAL_API_KEY not set")
        return
        
    client = Mistral(api_key=api_key)
    
    import inspect
    print(inspect.signature(client.ocr.process))

if __name__ == "__main__":
    main()
