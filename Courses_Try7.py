from pathlib import Path
import pytesseract as pyt
import cv2
import re
import matplotlib.pyplot as plt
import tkinter as tk
import numpy as np
from tkinter import messagebox, simpledialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog
from PIL import Image
import logging


class Options:
    def __init__(self, name, type_of_course, day, hours, group_numbers):
        self.name = name
        self.type_of_course = type_of_course
        self.day = day
        self.hours = hours
        self.group_numbers = group_numbers
        self.visible = False  # Start with options not visible

    def __repr__(self):
        return f"Course: {self.name}, Type: {self.type_of_course}, Day: {self.day}, Hours: {self.hours}, Group Numbers: {self.group_numbers}"


class TitleInputDialog(tk.Toplevel):
    def __init__(self, parent, image_paths):
        super().__init__(parent)
        self.title("Enter titles for images")
        self.image_paths = image_paths
        self.titles = []

        self.entries = []
        for i, path in enumerate(self.image_paths):
            tk.Label(self, text=f"Title for {path.name}:").grid(row=i, column=0, padx=10,
                                                                pady=5)  # Use path.name for the file name only
            entry = tk.Entry(self)
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entries.append(entry)

        self.submit_button = tk.Button(self, text="Submit", command=self.submit)
        self.submit_button.grid(row=len(self.image_paths), column=0, columnspan=2, pady=10)

    def submit(self):
        self.titles = [entry.get() for entry in self.entries]
        self.destroy()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_text(text, name_input):
    options_list = []
    sections = text.split("זמני לימוד:")
    for section in sections[1:]:
        day, hours, type_of_course, group_numbers = None, None, None, []

        lines = section.splitlines()
        for line in lines:
            day_hours_match = re.search(r"(יום \S)\s*(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})", line)
            if day_hours_match:
                day = day_hours_match.group(1)
                start_time = day_hours_match.group(2)
                end_time = day_hours_match.group(3)
                hours = f"{start_time} - {end_time}"

            type_group_match = re.search(r"(\d+)\s+(שעור|תרגיל|מעבדה)", line)
            if type_group_match:
                group_number = type_group_match.group(1)
                type_of_course = type_group_match.group(2)
                if group_number not in group_numbers:
                    group_numbers.append(group_number)

            if not (day_hours_match or type_group_match):
                logger.warning(f"Unmatched line in section: {line}")

        if day and hours and type_of_course:
            option = Options(name=name_input, type_of_course=type_of_course, day=day, hours=hours,
                             group_numbers=group_numbers)
            options_list.append(option)

    return options_list


logging.basicConfig(level=logging.INFO)


def process_image(image_path):
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"The image file does not exist: {image_path}")

    try:
        # Use Pillow to open the image (better support for various image formats)
        with Image.open(image_path) as img:
            # Convert to RGB if the image is in a different mode
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Convert to numpy array
            img_array = np.array(img)
    except Exception as e:
        logging.error(f"Failed to load the image {image_path}: {str(e)}")
        return ""

    # Convert to grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    # Apply multiple preprocessing techniques
    denoised = cv2.fastNlMeansDenoising(gray)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # Try different thresholding methods
    _, binary_otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    binary_adaptive = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # Resize the image (scaling up can sometimes improve OCR results)
    height, width = binary_adaptive.shape
    scale_factor = 1.5
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    resized = cv2.resize(binary_adaptive, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

    # Configure Tesseract OCR
    pyt.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

    # Try OCR with different preprocessing results
    text_results = []
    for img in [resized, cv2.resize(binary_otsu, (new_width, new_height), interpolation=cv2.INTER_CUBIC)]:
        try:
            text = pyt.image_to_string(img, lang='heb', config='--psm 6 --oem 3')
            text_results.append(text)
        except Exception as e:
            logging.error(f"OCR failed for {image_path}: {str(e)}")

    # Choose the result with more content
    final_text = max(text_results, key=len) if text_results else ""

    if not final_text.strip():
        logging.warning(f"No text extracted from {image_path}")

    return final_text


def plot_schedule(options_list, canvas, fig, ax):
    days_mapping = {'יום א': 0, 'יום ב': 1, 'יום ג': 2, 'יום ד': 3, 'יום ה': 4, 'יום ו': 5}
    plotted_blocks = []

    # Clear previous plot
    ax.clear()

    # Organize visible options by their day and check for collisions
    visible_options_by_day = {}
    for option in options_list:
        if option.visible:
            start_time, end_time = option.hours.split(' - ')
            start_hour = int(start_time.split(':')[0]) + int(start_time.split(':')[1]) / 60
            end_hour = int(end_time.split(':')[0]) + int(end_time.split(':')[1]) / 60

            day_index = days_mapping.get(option.day, -1)
            if day_index >= 0:
                if day_index not in visible_options_by_day:
                    visible_options_by_day[day_index] = []
                visible_options_by_day[day_index].append({
                    "start_hour": start_hour,
                    "end_hour": end_hour,
                    "option": option
                })

    # Plot all visible options
    for day_index, options in visible_options_by_day.items():
        num_options = len(options)
        block_width = 0.8 / num_options  # Divide the available width by the number of overlapping options
        for i, option_info in enumerate(options):
            start_hour = option_info['start_hour']
            end_hour = option_info['end_hour']
            option = option_info['option']

            # Offset each block horizontally
            x_offset = day_index + (i * block_width)

            # Fix Hebrew text for course type (reverse course type but keep the title intact)
            course_type_display = option.type_of_course[::-1]  # Reverse the Hebrew text for course type
            option_name_display = option.name[::-1]

            # Set color based on course type
            color = 'tab:blue' if option.type_of_course == 'שעור' else 'tab:green' if option.type_of_course == 'תרגיל' else 'tab:orange'

            # Plot the block
            ax.broken_barh([(x_offset, block_width)], (start_hour, end_hour - start_hour), facecolors=color)

            # Add text for group number, course type, and photo title in the plot
            ax.text(x_offset + block_width / 2, start_hour + (end_hour - start_hour) / 2,
                    f"{course_type_display}\nGroup: {', '.join(option.group_numbers)}\n{option_name_display}",
                    va='center', ha='center', color='white', fontsize=10, weight='bold')

    ax.set_xticks(range(6))
    ax.set_xticklabels(['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
    ax.set_yticks(range(8, 22))
    ax.set_ylim(8, 22)
    ax.set_ylabel('Time')
    ax.set_xlabel('Day')

    ax.grid(True)
    canvas.draw()


def toggle_option_visibility(option, all_options_list, canvas, fig, ax):
    # Toggle visibility for the clicked option
    option.visible = not option.visible

    # Gather all visible options from all images
    all_visible_options = []
    for data in all_options_list:
        for opt in data['options']:
            if opt.visible:
                all_visible_options.append(opt)

    # Plot the schedule with all currently visible options
    plot_schedule(all_visible_options, canvas, fig, ax)


def create_buttons(button_frame, grouped_options, all_options_list, canvas, fig, ax, column, photo_title):
    # Title labels and button styles for each type
    course_titles = {
        'שעור': 'Lectures',
        'תרגיל': 'Exercises',
        'מעבדה': 'Labs'
    }

    course_colors = {
        'שעור': 'lightblue',
        'תרגיל': 'lightgreen',
        'מעבדה': 'orange'
    }

    row = 1  # Start at row 1, because row 0 is the title

    for course_type, options in grouped_options.items():
        # Add title label for each course type
        title_label = tk.Label(button_frame, text=course_titles[course_type], font=("Helvetica", 12, "bold"))
        title_label.grid(row=row, column=column, padx=10, pady=5)

        row += 1  # Move to the next row for the buttons
        for option in options:
            button_text = f"{option.type_of_course} (Group {', '.join(option.group_numbers)})"
            toggle_button = tk.Button(button_frame, text=button_text, bg=course_colors[course_type], width=20,
                                      command=lambda opt=option: toggle_option_visibility(opt, all_options_list, canvas, fig, ax))
            toggle_button.grid(row=row, column=column, padx=10, pady=2)
            row += 1

    # Add the photo title above the buttons for the current image
    photo_title_label = tk.Label(button_frame, text=photo_title, font=("Helvetica", 14, "bold"))
    photo_title_label.grid(row=0, column=column, padx=10, pady=5)


def main():
    root = tk.Tk()
    root.withdraw()  # Hide the root window while asking for input

    # Ask the user to select multiple image files
    image_paths = filedialog.askopenfilenames(title="Select images for processing",
                                              filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])

    # Use Pathlib to handle file paths with Hebrew characters or non-ASCII characters
    image_paths = [Path(image_path) for image_path in image_paths]

    if not image_paths:
        messagebox.showerror("Error", "No images selected!")
        root.destroy()
        return

    # Create the custom dialog to get titles for all images
    title_dialog = TitleInputDialog(root, image_paths)
    root.wait_window(title_dialog)  # Wait for the dialog to close

    # Retrieve titles from the dialog
    titles = title_dialog.titles

    if not titles or any(title == "" for title in titles):
        messagebox.showerror("Error", "All images must have titles!")
        root.destroy()
        return

    all_options_list = []

    for i, image_path in enumerate(image_paths):
        extracted_text = process_image(image_path)
        options_list = parse_text(extracted_text, titles[i])

        # Add the options list with its associated title
        all_options_list.append({
            "title": titles[i],
            "options": options_list
        })

    root.deiconify()  # Show the root window now
    root.title("Weekly Schedule")

    fig, ax = plt.subplots()
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Create a frame for the buttons
    button_frame = tk.Frame(root)
    button_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Dynamically adjust the columns to be evenly spread
    total_photos = len(all_options_list)
    for i in range(total_photos):
        button_frame.grid_columnconfigure(i, weight=1, uniform="group1")  # Make columns evenly spread

    # Create buttons and display the schedule for all images
    for column, data in enumerate(all_options_list):  # Enumerate to get the column index for each image
        name_input = data["title"]
        options_list = data["options"]

        # Group options by course type (define grouped_options here)
        grouped_options = {
            'שעור': [],
            'תרגיל': [],
            'מעבדה': []
        }

        for option in options_list:
            if option.type_of_course in grouped_options:
                grouped_options[option.type_of_course].append(option)

        # Create buttons in their respective columns
        create_buttons(button_frame, grouped_options, all_options_list, canvas, fig, ax, column, name_input)

    root.mainloop()


# Example usage
main()
