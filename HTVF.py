import requests
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urljoin
import csv
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

HISTORY_FILE = "HowTo_search_history.csv"

# ----------- Core Logic -----------
def search_wikihow(query):
    query_encoded = urllib.parse.quote_plus(query)
    search_url = f"https://www.wikihow.com/wikiHowTo?search={query_encoded}"

    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    result_link = soup.select_one('.result_link')
    if not result_link or not result_link.get('href'):
        return None, None, None

    article_url = urljoin("https://www.wikihow.com", result_link['href'])
    summary, steps = extract_summary_and_steps(article_url)
    return article_url, summary, steps

def extract_summary_and_steps(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    summary_tag = soup.select_one('.mf-section-0 p')
    summary = summary_tag.get_text(strip=True) if summary_tag else "No summary found."

    steps = soup.select(".step b.whb")
    if not steps:
        steps = soup.select(".steps .step")

    instructions = [step.get_text(strip=True) for step in steps if step.get_text(strip=True)]
    return summary, instructions if instructions else ["No steps found."]

def save_to_csv(query, url, steps):
    exists = os.path.isfile(HISTORY_FILE)
    with open(HISTORY_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not exists:
            writer.writerow(["Timestamp", "Query", "URL", "Steps"])
        writer.writerow([datetime.now(), query, url, " | ".join(steps)])

def read_history():
    if not os.path.isfile(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, mode='r', encoding='utf-8') as file:
        reader = list(csv.reader(file))
        return reader[1:] if len(reader) > 1 else []

def delete_history_entry(index):
    if not os.path.isfile(HISTORY_FILE):
        return
    with open(HISTORY_FILE, mode='r', encoding='utf-8') as file:
        reader = list(csv.reader(file))
    header = reader[0]
    entries = reader[1:]
    if 0 <= index < len(entries):
        del entries[index]
        with open(HISTORY_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(entries)

# ----------- GUI -----------
def run_search():
    query = query_entry.get()
    if not query:
        messagebox.showwarning("Warning", "Please enter a search term.")
        return

    result_text.delete('1.0', tk.END)
    url, summary, steps = search_wikihow(query)

    if not url:
        result_text.insert(tk.END, "No article found.")
        return

    result_text.insert(tk.END, f"Summary:\n{summary}\n\nSteps:\n")
    for i, step in enumerate(steps, 1):
        result_text.insert(tk.END, f"{i}. {step}\n")

    save_to_csv(query, url, steps)
    update_history_list()

def update_history_list():
    history_list.delete(0, tk.END)
    history = read_history()
    for entry in history:
        history_list.insert(tk.END, f"{entry[1]} ({entry[0]})")

def show_history_entry(event):
    selection = history_list.curselection()
    if not selection:
        return
    index = selection[0]
    history = read_history()
    if index < len(history):
        entry = history[index]
        result_text.delete('1.0', tk.END)
        result_text.insert(tk.END, f"Replay: {entry[1]}\nURL: {entry[2]}\n\n")
        steps = entry[3].split(" | ")
        for i, step in enumerate(steps, 1):
            result_text.insert(tk.END, f"{i}. {step}\n")

def delete_selected_history():
    selection = history_list.curselection()
    if not selection:
        return
    index = selection[0]
    delete_history_entry(index)
    update_history_list()
    result_text.delete('1.0', tk.END)
    result_text.insert(tk.END, "✅ History entry deleted.\n")

# ----------- Setup GUI -----------
root = tk.Tk()
root.title("HowTo!!")
root.geometry("800x600")

frame = ttk.Frame(root)
frame.pack(padx=10, pady=10, fill='x')

query_label = ttk.Label(frame, text="Enter your how-to query:")
query_label.pack(anchor='w')

query_entry = ttk.Entry(frame, width=80)
query_entry.pack(fill='x')

search_button = ttk.Button(frame, text="Search", command=run_search)
search_button.pack(pady=5)

history_label = ttk.Label(frame, text="Search History:")
history_label.pack(anchor='w', pady=(10, 0))

history_list = tk.Listbox(frame, height=6)
history_list.pack(fill='x')
history_list.bind("<<ListboxSelect>>", show_history_entry)

delete_button = ttk.Button(frame, text="Delete Selected History", command=delete_selected_history)
delete_button.pack(pady=5)

result_label = ttk.Label(frame, text="Result:")
result_label.pack(anchor='w', pady=(10, 0))

result_text = scrolledtext.ScrolledText(frame, height=20)
result_text.pack(fill='both', expand=True)

update_history_list()
root.mainloop()
