# youslackingbro

a simple focus assist that actually works, both offline/ online to keep you focused.
**tl;dr**: keeps you focused. runs every 5 mins. yells at you if you slack off.

## setup

Most of the dependencies are auto installed and u can skip to usage as is, still if any issues:

1. **install dependencies**: `pip install .` (or `uv sync` if you're cool)
2. **install tesseract**: [download here](https://github.com/UB-Mannheim/tesseract/wiki), add to PATH.
3. **install ollama**: [download here](https://ollama.com/), run `ollama pull llama3.2` (or whatever model you want).
4. **env vars**: make a `.env` file if you want online mode:
   ```env
   GEMINI_API_KEY=your_key_here
   ```

## usage

* **run it**: `uv run main.py`
* **follow instructions**: tell it what you're doing.
* **chill**: it runs in background.

## modes

* **offline**: uses local ollama + tesseract. private. free.
* **online**: uses gemini api. faster. smarter.
