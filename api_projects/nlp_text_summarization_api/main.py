import openai
import os
import logging
import asyncio
import httpx
import sqlite3
import time
import signal
from dotenv import load_dotenv
from itertools import cycle
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Load environment variables from the .env file
load_dotenv()

# Set up logging for error reporting
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to handle graceful shutdown
def handle_exit(signum, frame):
    print(Fore.RED + "\nReceived exit signal. Cleaning up...")
    conn.close()
    exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# Initialize SQLite database and ensure the 'feedback' column exists
try:
    conn = sqlite3.connect('summaries.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS summaries
                      (id INTEGER PRIMARY KEY, original_text TEXT, summary TEXT, feedback TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS analysis
                      (id INTEGER PRIMARY KEY, timestamp TEXT, summary TEXT, tokens_used INTEGER)''')
    conn.commit()
except sqlite3.Error as e:
    logging.error(f"Database error: {e}")
    print(Fore.RED + "Failed to initialize the database. Please check the database file and permissions.")
    exit(1)

# API keys for rotation
api_keys = cycle([os.getenv('OPENAI_API_KEY'), os.getenv('OPENAI_API_KEY_2')])

# Manually specify available models and languages since dynamic fetching is not supported
available_models = ["gpt-3.5-turbo", "gpt-4"]
language_options = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "zh": "Chinese",
    "ja": "Japanese"
}

# Safe execution wrapper for database operations
def safe_execute(query, params):
    try:
        cursor.execute(query, params)
        conn.commit()
    except sqlite3.IntegrityError as e:
        logging.error(f"Integrity error: {e}")
        print(Fore.RED + "Data integrity issue occurred. Please check the input data.")
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        print(Fore.RED + "An error occurred while accessing the database.")

async def async_summarize_text(text, model="gpt-3.5-turbo", max_tokens=150, language="en", retries=5):
    api_key = next(api_keys)
    try:
        for attempt in range(retries):
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": f"You are a helpful assistant that summarizes text in {language_options.get(language, 'English')}."},
                                {"role": "user", "content": f"Summarize the following text:\n\n{text}"}
                            ],
                            "max_tokens": max_tokens,
                            "temperature": 0.5,
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    summary = data['choices'][0]['message']['content'].strip()
                    
                    tokens_used = data['usage']['total_tokens']
                    safe_execute("INSERT INTO summaries (original_text, summary) VALUES (?, ?)", (text, summary))
                    safe_execute("INSERT INTO analysis (timestamp, summary, tokens_used) VALUES (?, ?, ?)", 
                                 (time.strftime('%Y-%m-%d %H:%M:%S'), summary, tokens_used))
                    return summary
                except httpx.HTTPStatusError as e:
                    logging.error(f"HTTP error: {e.response.status_code}")
                    if response.status_code == 429:
                        logging.warning(f"Rate limit hit. Retrying in {2 ** attempt} seconds... (Attempt {attempt + 1} of {retries})")
                        time.sleep(2 ** attempt)
                    else:
                        raise
                except httpx.RequestError as e:
                    logging.error(f"Request error: {e}")
                    print(Fore.RED + "Network error occurred. Please check your internet connection.")
                    return None
        else:
            logging.error("Failed after multiple retries.")
            print(Fore.RED + "The operation failed after multiple attempts. Please try again later.")
            return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        print(Fore.RED + "An unexpected error occurred. Please try again later.")
        return None

async def async_summarize_texts_batch(texts, model="gpt-3.5-turbo", max_tokens=150, language="en"):
    tasks = [async_summarize_text(text, model, max_tokens, language) for text in texts]
    return await asyncio.gather(*tasks)

def collect_feedback(summary_id):
    feedback = input(f"Please provide your feedback on the summary for Summary ID {summary_id}. You can share your thoughts on its accuracy, completeness, or how useful you found it: ")
    safe_execute("UPDATE summaries SET feedback = ? WHERE id = ?", (feedback, summary_id))

def analyze_summaries():
    try:
        cursor.execute("SELECT timestamp, summary, tokens_used FROM analysis")
        rows = cursor.fetchall()
        print("\nAnalysis of Summaries:")
        for row in rows:
            print(f"Timestamp: {row[0]}, Tokens Used: {row[2]}")
            print(f"Summary: {row[1]}\n")
    except sqlite3.Error as e:
        logging.error(f"Database error during analysis: {e}")
        print(Fore.RED + "An error occurred while analyzing the summaries.")

def run_cli():
    print(Style.BRIGHT + Fore.BLUE + "Welcome to the NLP Text Summarization CLI!\n")

    # Display available models
    print(Fore.CYAN + "Available models:")
    for i, model in enumerate(available_models, 1):
        print(f"{Fore.YELLOW}{i}. {model} - Recommended for general use.")

    # Model selection with validation
    while True:
        model_choice = input(f"\n{Fore.CYAN}Enter the model number to use (default: 1, or type 'help' for options): ") or "1"
        if model_choice.lower() == "help":
            print(Fore.GREEN + "\nModel 1 (gpt-3.5-turbo): Suitable for most general-purpose text summarization.")
            print(Fore.GREEN + "Model 2 (gpt-4): Offers enhanced capabilities but may have higher usage costs.")
            continue
        try:
            model_choice = int(model_choice) - 1
            if 0 <= model_choice < len(available_models):
                model = available_models[model_choice]
                break
            else:
                print(Fore.RED + "Invalid choice, please enter a number corresponding to a listed model.")
        except ValueError:
            print(Fore.RED + "Invalid input, please enter a number.")
    
    # Prompt for max tokens with validation
    while True:
        try:
            max_tokens = int(input(f"\n{Fore.CYAN}Enter the maximum tokens for the summary (50 to 300, default: 150): ") or "150")
            if 50 <= max_tokens <= 300:
                break
            else:
                print(Fore.RED + "Please enter a number between 50 and 300.")
        except ValueError:
            print(Fore.RED + "Invalid input. Please enter a valid number.")
    
    # Display language options with enhanced help
    print(Fore.CYAN + "\nAvailable languages:")
    for code, language in language_options.items():
        print(f"{Fore.YELLOW}{code}: {language}")

    while True:
        language = input(f"\n{Fore.CYAN}Enter the language code for the text (default: en, or type 'help' for more information): ") or "en"
        if language.lower() == "help":
            print(Fore.GREEN + "\nHelp for Language Selection:")
            print(f"{Fore.YELLOW}English (en): Best suited for general English content.")
            print(f"{Fore.YELLOW}Spanish (es): Ideal for summarizing content written in Spanish.")
            print(f"{Fore.YELLOW}French (fr): Choose this if your content is in French.")
            print(f"{Fore.YELLOW}German (de): Use this option for German language content.")
            print(f"{Fore.YELLOW}Chinese (zh): Suitable for Chinese text summarization.")
            print(f"{Fore.YELLOW}Japanese (ja): Select this for Japanese text content.\n")
            continue
        if language in language_options:
            break
        else:
            print(Fore.RED + "Invalid language code, please enter a valid option or type 'help' for assistance.")

    texts = []
    while True:
        text = input(f"\n{Fore.CYAN}Enter text to summarize: ")
        texts.append(text)
        
        more_texts = input(f"{Fore.CYAN}Would you like to summarize another text? (y/n, default: n): ").lower() or "n"
        if more_texts == 'n':
            break
    
    # Confirm choices
    print(Fore.CYAN + "\nYou have chosen the following settings:")
    print(f"{Fore.YELLOW}Model: {model}")
    print(f"{Fore.YELLOW}Maximum Tokens: {max_tokens}")
    print(f"{Fore.YELLOW}Language: {language_options[language]}")
    print(f"{Fore.YELLOW}Number of texts to summarize: {len(texts)}")
    confirm = input(f"\n{Fore.CYAN}Do you want to proceed? (y/n, default: y): ").lower() or "y"
    if confirm != 'y':
        print(Fore.RED + "\nOperation canceled by user.")
        return

    summaries = asyncio.run(async_summarize_texts_batch(texts, model, max_tokens, language))
    
    print(Fore.CYAN + "\nSummarized Texts:")
    for i, summary in enumerate(summaries, 1):
        print(f"{Fore.GREEN}Summary {i}: {summary}")
        collect_feedback(i)

    # Analyze summaries if requested
    analyze_choice = input(f"\n{Fore.CYAN}Would you like to analyze the summaries? (y/n, default: n): ").lower() or "n"
    if analyze_choice == 'y':
        analyze_summaries()

if __name__ == "__main__":
    run_cli()

# Close the database connection when done
conn.close()
