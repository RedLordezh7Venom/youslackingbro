# testing guide

how to make sure this thing actually works.

## 1. offline mode (local / ollama)

* **prereq**: ensure `ollama` is running (`ollama serve`). check if `pytesseract` can see your tesseract install (`tesseract --version` in terminal).
* **run**: `python main.py`
* **select**: `offline`
* **prompt**: type "writing code"
* **action**: open a youtube video or reddit. wait 5 mins.
* **verify**: did you get a toast notification roasting you?

## 2. online mode (gemini)

* **prereq**: valid `GEMINI_API_KEY` in `.env`.
* **run**: `python main.py`
* **select**: `online`
* **prompt**: type "working on spreadsheet"
* **action**: play a game. wait 5 mins.
* **verify**: check for toast notification.

## 3. debug / fast testing

if you don't wanna wait 5 mins:
* open `main.py`
* find `time.sleep(300)`
* change to `time.sleep(10)`
* run again.
