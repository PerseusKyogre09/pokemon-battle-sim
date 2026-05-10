import os
import sys
import uvicorn

# Add the current directory to sys.path so it can find the 'src' package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting Pokémon Battle Sim Backend...")
    # This imports the app from the package and runs it
    # Port 7860 is used for Hugging Face compatibility
    uvicorn.run("src.core.fastapi_server:app", host="0.0.0.0", port=7860, reload=True)
