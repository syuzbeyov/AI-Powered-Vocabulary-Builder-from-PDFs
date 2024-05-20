import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import json
import os
import configparser
import random
import pyttsx3
from PyPDF2 import PdfReader
from api import create_language_learning_content
import textwrap
from PIL import Image, ImageDraw, ImageFont
from pdfminer.high_level import extract_text
import re
from tkinter.ttk import Progressbar

class CreateToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.wait_time = 500     # milliseconds
        self.wrap_length = 180   # pixels
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.schedule = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)

    def enter(self, event=None):
        self.schedule = self.widget.after(self.wait_time, self.create_tooltip)

    def create_tooltip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")  # Get widget size
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # Creates a toplevel window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background="#ffffff", relief='solid', borderwidth=1,
                         wraplength=self.wrap_length)
        label.pack(ipadx=1)

    def close(self, event=None):
        if self.schedule:
            self.widget.after_cancel(self.schedule)
            self.schedule = None
        if self.tooltip_window and self.tooltip_window.winfo_exists():
            self.tooltip_window.destroy()
            self.tooltip_window = None



class LanguageLearningApp:
    def __init__(self):
        ctk.set_appearance_mode("System")  # Enable dark mode support
        ctk.set_default_color_theme("dark-blue")  # Set the color theme
        self.app = ctk.CTk()
        self.app.title("Language Learning App")
        self.languages = ["English", "Spanish", "French", "German", "Italian"]
        self.user_data = {}
        self.current_user = tk.StringVar(self.app)
        self.setup_ui()
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.app.mainloop()

    def setup_ui(self):
        self.user_interaction_frame = ctk.CTkFrame(self.app)
        self.user_interaction_frame.grid(row=0, column=0, sticky='ew')
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use a modern theme
        self.button_font = ("Montserrat", 20, "bold")  # Specify the Nunito font family, size, and style
        self.listbox_font = ("Merriweather", 16)  # Define the font settings for Listboxes
        self.text_widget_font = ("Merriweather", 16)  # Define the font settings for the Text widget

        self.appearance_mode_switch = ctk.CTkSwitch(self.user_interaction_frame, text="Dark Mode", command=self.switch_appearance_mode, font=self.button_font)
        self.appearance_mode_switch.grid(row=0, column=8, padx=5, pady=5)

        self.login_button = ctk.CTkButton(self.user_interaction_frame, text="LOGIN", width=100, height=45, command=self.login_user, font=self.button_font)
        self.login_button.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        self.language_var = tk.StringVar()
        self.language_menu = ttk.Combobox(self.user_interaction_frame, textvariable=self.language_var, values=self.languages, state="readonly")
        self.language_menu.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

        self.set_language_button = ctk.CTkButton(self.user_interaction_frame, text="Set Language", command=self.choose_language, state=ctk.DISABLED, border_color="black", font=self.button_font)
        self.set_language_button.grid(row=0, column=2, padx=5, pady=5, sticky='nsew')

        self.upload_button = ctk.CTkButton(self.user_interaction_frame, text="Upload PDF", command=self.upload_pdf, state=ctk.DISABLED, border_color="black", font=self.button_font)
        self.upload_button.grid(row=0, column=3, padx=5, pady=5, sticky='nsew')

        self.highlight_button = ctk.CTkButton(self.user_interaction_frame, text="Highlight Text", command=self.highlight_text, state=ctk.DISABLED, border_color="black", font=self.button_font)
        self.highlight_button.grid(row=0, column=4, padx=5, pady=5, sticky='nsew')

        self.pronounce_button = ctk.CTkButton(self.user_interaction_frame, text="Pronounce Word", command=self.pronounce_word, state=ctk.DISABLED, border_color="black", font=self.button_font)
        self.pronounce_button.grid(row=0, column=5, padx=5, pady=5, sticky='nsew')

        self.show_definitions_button = ctk.CTkButton(self.user_interaction_frame, text="Show Definitions", command=self.show_definitions, state=ctk.DISABLED, border_color="black", font=self.button_font)
        self.show_definitions_button.grid(row=0, column=6, padx=5, pady=5, sticky='nsew')

        self.start_quiz_button = ctk.CTkButton(self.user_interaction_frame, text="Start Quiz", command=self.start_quiz, state=ctk.DISABLED, border_color="black", font=self.button_font)
        self.start_quiz_button.grid(row=0, column=7, padx=5, pady=5, sticky='nsew')

        self.app.grid_rowconfigure(1, weight=1)
        self.app.grid_columnconfigure(0, weight=1)
        for i in range(9):
            self.user_interaction_frame.grid_columnconfigure(i, weight=1, uniform="group1")

        self.main_frame = ctk.CTkFrame(self.app)
        self.main_frame.grid(row=1, column=0, sticky='nsew')
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=1)

        self.text_box = tk.Text(self.main_frame, wrap='word', font=self.text_widget_font)
        self.text_box.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        self.words_frame = ctk.CTkFrame(self.main_frame)
        self.words_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        self.words_frame.grid_rowconfigure([0, 1], weight=1)
        self.words_frame.grid_columnconfigure(0, weight=1)
        self.words_frame.grid_columnconfigure(1, weight=1)

        self.words_to_be_learned_frame = ctk.CTkFrame(self.words_frame)
        self.words_to_be_learned_frame.grid(row=0, column=0, sticky='nsew')

        self.title_label_words_to_be_learned = ctk.CTkLabel(self.words_to_be_learned_frame, text="Words to be Learned", font=self.button_font)
        self.title_label_words_to_be_learned.pack(side=tk.TOP, fill=tk.X)

        self.words_to_be_learned_listbox = tk.Listbox(self.words_to_be_learned_frame, height=10, width=50, selectmode='multiple', font=self.listbox_font)
        self.words_to_be_learned_listbox.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.words_to_be_learned_listbox.bind('<Delete>', lambda event: self.delete_selected_words(event, 'to_learn'))

        self.learned_words_frame = ctk.CTkFrame(self.words_frame)
        self.learned_words_frame.grid(row=1, column=0, sticky='nsew')

        self.title_label_learned_words = ctk.CTkLabel(self.learned_words_frame, text="Learned Words", font=self.button_font)
        self.title_label_learned_words.pack(side=tk.TOP, fill=tk.X)

        self.learned_words_listbox = tk.Listbox(self.learned_words_frame, height=10, width=50, font=self.listbox_font)
        self.learned_words_listbox.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.learned_words_listbox.bind('<Delete>', lambda event: self.delete_selected_words(event, 'learned'))

        self.generate_story_button = ctk.CTkButton(self.learned_words_frame, text="Generate a Story", command=self.generate_story_app, state=ctk.DISABLED, border_color="black", font=self.button_font)
        self.generate_story_button.pack(fill=tk.X, padx=0, pady=(0, 10))

        self.generate_flashcards_button = ctk.CTkButton(self.learned_words_frame, text="Generate Flash Cards", command=self.generate_flash_cards, state=ctk.DISABLED, border_color="black", font=self.button_font)
        self.generate_flashcards_button.pack(fill=tk.X, padx=0, pady=0)

        self.learning_progress_bar = Progressbar(self.words_to_be_learned_frame, orient='horizontal', length=200, mode='determinate')
        self.learning_progress_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        self.api_key_frame = ctk.CTkFrame(self.app)
        self.api_key_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        self.api_key_label = ctk.CTkLabel(self.api_key_frame, text="API Key:", font=self.button_font)
        self.api_key_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.api_key_entry = ctk.CTkEntry(self.api_key_frame, font=self.button_font, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.save_api_key_button = ctk.CTkButton(self.api_key_frame, text="Save API Key", command=self.save_api_key, font=self.button_font)
        self.save_api_key_button.grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.api_key_frame.grid_columnconfigure(1, weight=1)
        
        self.app.update_idletasks()

        self.app.bind('<Control-u>', self.upload_pdf)
        self.app.bind('<Control-s>', self.highlight_text)
        self.app.bind('<Control-l>', self.login_user)
        self.app.bind('<Control-p>', self.pronounce_word)
        self.app.bind('<Control-d>', self.show_definitions)
        self.app.bind('<Control-g>', self.generate_story_app)
        self.app.bind('<Control-q>', self.start_quiz)
        self.app.bind('<Control-f>', self.generate_flash_cards)

        self.login_button_tooltip = CreateToolTip(self.login_button, "To start a new session. The data generated will be saved in this profile so that you can continue the study later. Shortcut Key: ctrl+L")
        self.generate_story_button_tooltip = CreateToolTip(self.generate_story_button, "Generate short stories from selected words. You can select from a minimum of 5 to a maximum of 10 words. Shortcut key: ctrl+G")
        self.set_language_button_tooltip = CreateToolTip(self.set_language_button, "Set your preferred language for the application. This setting will affect the language used for word definitions, pronunciations, and quizzes.")
        self.upload_button_tooltip = CreateToolTip(self.upload_button, "Upload a PDF from which you want to learn new words. The application will extract words from the document for your learning list. Shortcut Key: ctrl+U")
        self.highlight_button_tooltip = CreateToolTip(self.highlight_button, "Highlight a selected word in the PDF text. Highlighted words can be added to your list of words to learn. Shortcut Key: ctrl+S")
        self.pronounce_button_tooltip = CreateToolTip(self.pronounce_button, "Hear the pronunciation of a selected word. Make sure to select a word in the text before clicking this button. Shortcut Key: ctrl+P")
        self.show_definitions_button_tooltip = CreateToolTip(self.show_definitions_button, "Show definitions for the first five words in your 'Words to be Learned' list. Use this to study and understand your new vocabulary better. Shortcut Key: ctrl+D")
        self.start_quiz_button_tooltip = CreateToolTip(self.start_quiz_button, "Start a quiz on the words you've been learning. This is a great way to test your knowledge and reinforce learning. Shortcut Key: ctrl+Q")
        self.generate_flashcards_button_tooltip = CreateToolTip(self.generate_flashcards_button, "Generate Flash Cards of the selected words (will be saved under {'User}/Flashcards). Shortcut Key: ctrl+F")

        self.app.minsize(800, 600)

    def login_user(self, event=None):
        username = simpledialog.askstring("Login", "Enter your username")
        if username:
            self.current_user.set(username)
            user_specific_data = self.load_user_data(username)
            self.user_data[username] = user_specific_data
            self.update_ui_for_user()

    def load_user_data(self, username):
        sanitized_username = self.sanitize_username(username)
        file_path = os.path.join("./Profiles", sanitized_username, 'user_data.json')
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {'words': [], 'language': None, 'learned_words': []}

    def save_user_data(self, username):
        sanitized_username = self.sanitize_username(username)
        user_directory = os.path.join("./Profiles", sanitized_username)
        os.makedirs(user_directory, exist_ok=True)
        file_path = os.path.join(user_directory, 'user_data.json')
        try:
            with open(file_path, 'w') as file:
                json.dump(self.user_data[username], file)
        except IOError as e:
            messagebox.showerror("Error", f"Failed to save user data: {e}")

    def sanitize_username(self, username):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            username = username.replace(char, '')
        username = username.strip().replace(' ', '_')
        return username

    def update_ui_for_user(self):
        username = self.current_user.get()
        if username in self.user_data:
            self.set_language_button.configure(state=ctk.NORMAL)
            self.upload_button.configure(state=ctk.NORMAL)
            self.highlight_button.configure(state=ctk.NORMAL)
            self.show_definitions_button.configure(state=ctk.NORMAL)
            self.start_quiz_button.configure(state=ctk.NORMAL)
            self.generate_story_button.configure(state=ctk.NORMAL)
            self.generate_flashcards_button.configure(state=ctk.NORMAL)

            user_lang = self.user_data[username].get('language')
            if user_lang:
                self.language_var.set(user_lang)
                self.language_menu.set(user_lang)
                self.pronounce_button.configure(state=ctk.NORMAL)
            else:
                self.language_var.set('')
                self.pronounce_button.configure(state=ctk.DISABLED)

            self.update_listboxes_based_on_user_data(username)
            self.update_quiz_state()
            self.update_progress_bar()

    def save_api_key(self):
        api_key = self.api_key_entry.get()
        if api_key:
            self.update_api_key_in_config(api_key)
            messagebox.showinfo("Success", "API key saved successfully.")
        else:
            messagebox.showwarning("Warning", "Please enter a valid API key.")

    def update_api_key_in_config(self, api_key):
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')
        config.read(config_path)

        if 'ApiKeys' not in config:
            config['ApiKeys'] = {}
        config['ApiKeys']['gpt_api_key'] = api_key

        with open(config_path, 'w') as configfile:
            config.write(configfile)

    def update_api_py(self, api_key):
        api_py_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'api.py')
        
        with open(api_py_path, 'r') as file:
            api_py_contents = file.read()
        
        # Replace the placeholder text with the new API key
        new_api_py_contents = api_py_contents.replace("your_api_key = 'UPDATEEEEE'", f"your_api_key = '{api_key}'")
        
        with open(api_py_path, 'w') as file:
            file.write(new_api_py_contents)
            
    def upload_pdf(self, event=None):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            user_specific_words = self.extract_words_from_pdf(file_path)
            self.user_data[self.current_user.get()]['words_list'] = user_specific_words
            self.display_pdf(file_path)
            self.save_user_data(self.current_user.get())

    def display_pdf(self, file_path):
        reader = PdfReader(file_path)
        num_pages = len(reader.pages)
        page_text = ""
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            page_text += page.extract_text() + "\n\n"
        self.text_box.delete(1.0, tk.END)
        self.text_box.insert(tk.END, page_text)

    def extract_words_from_pdf(self, file_path):
        text = extract_text(file_path)
        words = self.extract_words(text)
        unique_words = list(set(words))
        limited_words = unique_words[:200]
        return limited_words

    def extract_words(self, text):
        words = re.findall(r'\b\w+\b', text.lower())
        return words

    def highlight_text(self, event=None):
        try:
            start_index = self.text_box.index("sel.first")
            end_index = self.text_box.index("sel.last")
            selected_text = self.text_box.get(start_index, end_index).strip().lower()

            if not selected_text:
                messagebox.showerror("Error", "No text selected")
                return

            if self.current_user.get() in self.user_data and 'words' in self.user_data[self.current_user.get()]:
                if selected_text in self.user_data[self.current_user.get()]['words']:
                    messagebox.showinfo("Info", f"'{selected_text}' is already in your 'Words to be Learned' list.")
                    return
                elif selected_text in self.user_data[self.current_user.get()].get('learned_words', []):
                    messagebox.showinfo("Info", f"'{selected_text}' is already in your 'Learned Words' section.")
                    return
                else:
                    self.user_data[self.current_user.get()]['words'].append(selected_text)
                    self.words_to_be_learned_listbox.insert(tk.END, selected_text)
                    self.text_box.tag_add("highlight", start_index, end_index)
                    self.text_box.tag_config("highlight", background="yellow")
            else:
                messagebox.showerror("Error", "User not logged in or word list not initialized")
        except tk.TclError:
            messagebox.showerror("Error", "No text selected")
        self.update_quiz_state()

    def show_definitions(self, event=None):
        username = self.current_user.get()
        if not username:
            messagebox.showinfo("Info", "Please login first.")
            return
        if 'words' not in self.user_data[username] or not self.user_data[username]['words']:
            messagebox.showinfo("Info", "No words to learn.")
            return

        definitions_window = tk.Toplevel(self.app)
        definitions_window.title("Word Definitions")

        words_definitions = [(word, self.get_word_definition(username, word, self.user_data[username]['language']))
                             for word in self.user_data[username]['words'][:5]]

        current_word_index = [0]

        def update_display():
            for widget in definitions_window.winfo_children():
                if widget != continue_button:
                    widget.destroy()

            if current_word_index[0] < len(words_definitions):
                word, definition = words_definitions[current_word_index[0]]
                word_number = current_word_index[0] + 1
                word_label = tk.Label(definitions_window, text=f"Word {word_number}: {word} - {definition}")
                word_label.pack()

                current_word_index[0] += 1

                if current_word_index[0] >= len(words_definitions):
                    continue_button.configure(state='disabled')
            else:
                continue_button.configure(state='disabled')

        continue_button = tk.Button(definitions_window, text="Continue", command=update_display)
        continue_button.pack(side=tk.BOTTOM)

        update_display()

    def start_quiz(self, event=None):
        username = self.current_user.get()
        if not username or 'words' not in self.user_data[username] or not self.user_data[username]['words']:
            messagebox.showinfo("Info", "No words to start the quiz.")
            return

        quiz_words = self.user_data[username]['words'][:5]
        quiz_definitions = [self.user_data[username]['definitions'].get(word) for word in quiz_words]

        quiz_window = tk.Toplevel(self.app)
        quiz_window.title("Quiz")

        question_label = tk.Label(quiz_window, text="")
        question_label.pack()

        option_buttons = [tk.Button(quiz_window, text="Option", width=20) for _ in range(5)]
        for button in option_buttons:
            button.pack()

        current_question_index = [0]

        def generate_question():
            if current_question_index[0] < len(quiz_words):
                word = quiz_words[current_question_index[0]]
                definition = quiz_definitions[current_question_index[0]]
                try:
                    part_of_interest = definition.split("Example sentence in Italian:")[1].split("Example sentence in English:")[0]
                except IndexError:
                    part_of_interest = definition

                question_text = part_of_interest.replace(word, '----------').strip()
                correct_answer = word

                distractors = random.sample([w for w in self.user_data[username]['words_list'] if w != word], 4)
                options = distractors + [correct_answer]
                random.shuffle(options)

                question_label.config(text=question_text)
                for i, button in enumerate(option_buttons):
                    button.config(text=options[i], command=lambda opt=options[i]: handle_user_choice(opt, correct_answer))
            else:
                messagebox.showinfo("Quiz Complete", "You have completed the quiz!")
                quiz_window.destroy()

        def handle_user_choice(selected_option, correct_answer):
            if selected_option == correct_answer:
                messagebox.showinfo("Correct", "That's correct!")
                if correct_answer in self.user_data[username]['words']:
                    self.user_data[username]['words'].remove(correct_answer)
                    self.user_data[username].setdefault('learned_words', []).append(correct_answer)
                    self.update_listboxes()
                    self.save_user_data(username)
                    self.update_progress_bar()

                current_question_index[0] += 1
                if current_question_index[0] < len(quiz_words):
                    generate_question()
                else:
                    messagebox.showinfo("Quiz Complete", "You have completed the quiz!")
                    quiz_window.destroy()
            else:
                messagebox.showinfo("Incorrect", "That's not correct. Try again.")

        generate_question()

    def update_listboxes(self):
        self.words_to_be_learned_listbox.delete(0, tk.END)
        self.learned_words_listbox.delete(0, tk.END)
        username = self.current_user.get()
        for word in self.user_data[username].get('words', []):
            self.words_to_be_learned_listbox.insert(tk.END, word)
        for word in self.user_data[username].get('learned_words', []):
            self.learned_words_listbox.insert(tk.END, word)

    def generate_story_app(self, event=None):
        selected_indices = self.words_to_be_learned_listbox.curselection()
        selected_words = [self.words_to_be_learned_listbox.get(i) for i in selected_indices]

        if len(selected_words) < 5 or len(selected_words) > 10:
            messagebox.showerror("Error", "Please select a minimum of 5 words and a maximum of 10 words.")
            return

        story_words = ' '.join(selected_words)
        self.update_ini_file(story_words)
        messagebox.showinfo("Success", "Your story words have been updated.")

    def generate_flash_cards(self, event=None):
        selected_indices = self.learned_words_listbox.curselection()
        selected_words = [self.learned_words_listbox.get(i) for i in selected_indices]

        if not selected_words:
            messagebox.showwarning("Warning", "Please select at least one word.")
            return

        flashcards_dir = os.path.join("./Profiles", self.sanitize_username(self.current_user.get()), "Flashcards")
        os.makedirs(flashcards_dir, exist_ok=True)

        for word in selected_words:
            definition = self.user_data[self.current_user.get()].get('definitions', {}).get(word, "No definition found.")
            image = self.create_flashcard_image(word, definition)
            image_path = os.path.join(flashcards_dir, f"{word}.png")
            image.save(image_path)

        messagebox.showinfo("Success", "Flash cards generated successfully.")

    def create_flashcard_image(self, word, definition, width=500, height=700):
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()

        draw.text((10, 10), word, fill="black", font=font)
        wrapped_definition = "\n".join(textwrap.wrap(definition, width=40))
        draw.text((10, 50), wrapped_definition, fill="black", font=font)

        return image

    def update_quiz_state(self):
        if len(self.words_to_be_learned_listbox.get(0, tk.END)) >= 5:
            self.show_definitions_button.configure(state=tk.NORMAL)
        else:
            self.show_definitions_button.configure(state=tk.DISABLED)

    def update_listboxes_based_on_user_data(self, username):
        self.words_to_be_learned_listbox.delete(0, tk.END)
        self.learned_words_listbox.delete(0, tk.END)

        if username in self.user_data:
            if 'words' in self.user_data[username]:
                for word in self.user_data[username]['words']:
                    self.words_to_be_learned_listbox.insert(tk.END, word)

            if 'learned_words' in self.user_data[username]:
                for word in self.user_data[username]['learned_words']:
                    self.learned_words_listbox.insert(tk.END, word)

    def choose_language(self):
        if not self.current_user.get():
            messagebox.showwarning("Warning", "Please login first")
            return
        selected_language = self.language_menu.get()
        if selected_language:
            self.user_data[self.current_user.get()]['language'] = selected_language
            messagebox.showinfo("Info", f"Language set to {selected_language}")
            self.pronounce_button.configure(state=ctk.NORMAL)
        else:
            messagebox.showerror("Error", "No language selected")
            self.pronounce_button.configure(state=ctk.DISABLED)

    def pronounce_word(self, event=None):
        try:
            start_index = self.text_box.index("sel.first")
            end_index = self.text_box.index("sel.last")
            selected_word = self.text_box.get(start_index, end_index)

            engine = pyttsx3.init()
            user_language = self.user_data[self.current_user.get()]['language']

            for voice in engine.getProperty('voices'):
                if user_language in voice.name:
                    engine.setProperty('voice', voice.id)
                    break

            engine.say(selected_word)
            engine.runAndWait()
        except tk.TclError:
            messagebox.showerror("Error", "No word selected")
        except KeyError:
            messagebox.showerror("Error", "User not logged in or language not set")

    def get_word_definition(self, username, word, language_var):
        if word in self.user_data[username].get('definitions', {}):
            return self.user_data[username]['definitions'][word]
        definition = create_language_learning_content(word, language_var)
        self.user_data[username].setdefault('definitions', {})[word] = definition
        self.save_user_data(username)
        return definition

    def update_ini_file(self, story_words):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(dir_path, 'config.ini')

        config = configparser.ConfigParser()
        config.read(config_path)

        if 'Story' not in config:
            config['Story'] = {}
        config['Story']['main_keyword'] = story_words

        with open(config_path, 'w') as configfile:
            config.write(configfile)

    def switch_appearance_mode(self):
        switch_value = self.appearance_mode_switch.get()
        if switch_value:
            ctk.set_appearance_mode("dark")
            self.text_box.config(bg='black', fg='white')
            self.words_to_be_learned_listbox.config(bg='black', fg='white')
            self.learned_words_listbox.config(bg='black', fg='white')
        else:
            ctk.set_appearance_mode("light")
            self.text_box.config(bg='white', fg='black')
            self.words_to_be_learned_listbox.config(bg='white', fg='black')
            self.learned_words_listbox.config(bg='white', fg='black')

    def update_progress_bar(self):
        total_words = len(self.words_to_be_learned_listbox.get(0, tk.END)) + len(self.learned_words_listbox.get(0, tk.END))
        learned_words = len(self.learned_words_listbox.get(0, tk.END))

        if total_words > 0:
            progress = (learned_words / total_words) * 100
        else:
            progress = 0

        self.learning_progress_bar['value'] = progress
        self.app.update_idletasks()

    def delete_selected_words(self, event, listbox_type):
        selected_indices = []
        if listbox_type == 'to_learn':
            selected_indices = self.words_to_be_learned_listbox.curselection()
            listbox = self.words_to_be_learned_listbox
            word_list_key = 'words'
        elif listbox_type == 'learned':
            selected_indices = self.learned_words_listbox.curselection()
            listbox = self.learned_words_listbox
            word_list_key = 'learned_words'

        for index in reversed(selected_indices):
            listbox.delete(index)
            if self.current_user.get() in self.user_data:
                word_to_remove = self.user_data[self.current_user.get()][word_list_key][index]
                self.user_data[self.current_user.get()][word_list_key].remove(word_to_remove)
                self.save_user_data(self.current_user.get())

        self.update_listboxes_based_on_user_data(self.current_user.get())
        self.update_quiz_state()
        self.update_progress_bar()

    def on_closing(self):
        if self.current_user.get():
            self.save_user_data(self.current_user.get())
        self.app.destroy()

if __name__ == "__main__":
    app = LanguageLearningApp()
