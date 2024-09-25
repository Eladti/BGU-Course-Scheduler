import pytesseract as pyt
import cv2
import re
import matplotlib
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog


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
            tk.Label(self, text=f"Title for {path.split('/')[-1]}:", font=("Helvetica", 12)).grid(row=i, column=0, padx=10, pady=5)
            entry = tk.Entry(self, font=("Helvetica", 12))
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entries.append(entry)

        self.submit_button = tk.Button(self, text="Submit", font=("Helvetica", 12), command=self.submit)
        self.submit_button.grid(row=len(self.image_paths), column=0, columnspan=2, pady=10)

    def submit(self):
        self.titles = [entry.get() for entry in self.entries]
        self.destroy()


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

        if day and hours and type_of_course:
            option = Options(name=name_input, type_of_course=type_of_course, day=day, hours=hours,
                             group_numbers=group_numbers)
            options_list.append(option)

    return options_list


def process_image(image_path):
    pyt.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    height, width = thresh.shape
    new_width = int(width * 1.5)
    new_height = int(height * 1.5)
    resized = cv2.resize(thresh, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

    text = pyt.image_to_string(resized, lang='heb', config='--psm 6')
    return text


def plot_schedule(options_list, canvas, fig, ax):
    days_mapping = {'יום א': 0, 'יום ב': 1, 'יום ג': 2, 'יום ד': 3, 'יום ה': 4, 'יום ו': 5}
    plotted_blocks = []

    ax.clear()

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

    for day_index, options in visible_options_by_day.items():
        num_options = len(options)
        block_width = 0.8 / num_options
        for i, option_info in enumerate(options):
            start_hour = option_info['start_hour']
            end_hour = option_info['end_hour']
            option = option_info['option']

            x_offset = day_index + (i * block_width)

            course_type_display = option.type_of_course[::-1]
            option_name_display = option.name[::-1]

            # Set modern colors with transparency
            color = 'tab:blue' if option.type_of_course == 'שעור' else 'tab:green' if option.type_of_course == 'תרגיל' else 'tab:orange'
            color = matplotlib.colormaps.get_cmap('Pastel1')(i / num_options)

            # Plot the block with a cleaner, modern feel
            ax.broken_barh([(x_offset, block_width)], (start_hour, end_hour - start_hour), facecolors=color, alpha=0.75)

            # Add text for group number, course type, and photo title in the plot
            ax.text(x_offset + block_width / 2, start_hour + (end_hour - start_hour) / 2,
                    f"{course_type_display}\nGroup: {', '.join(option.group_numbers)}\n{option_name_display}",
                    va='center', ha='center', color='black', fontsize=10, weight='bold')

    # Modernize gridlines and labels
    ax.set_xticks(range(6))
    ax.set_xticklabels(['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], fontweight='bold')
    ax.set_yticks(range(8, 22))
    ax.set_ylim(8, 22)
    ax.set_ylabel('Time', fontsize=12, fontweight='bold')
    ax.set_xlabel('Day', fontsize=12, fontweight='bold')

    ax.grid(True, linestyle='--', color='lightgray')
    ax.set_facecolor('#f4f4f4')  # Light background for the plot

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

    # Add the photo title above the buttons for the current image
    photo_title_label = tk.Label(button_frame, text=photo_title, font=("Helvetica", 14, "bold"))
    photo_title_label.grid(row=0, column=column, padx=10, pady=10)

    row = 1  # Start at row 1, because row 0 is the title

    for course_type, options in grouped_options.items():
        # Add title label for each course type
        title_label = tk.Label(button_frame, text=course_titles[course_type], font=("Helvetica", 12, "bold"))
        title_label.grid(row=row, column=column, padx=10, pady=5)

        row += 1  # Move to the next row for the buttons
        for option in options:
            button_text = f"{option.type_of_course} (Group {', '.join(option.group_numbers)})"
            toggle_button = tk.Button(button_frame, text=button_text, bg=course_colors[course_type], width=20,
                                      font=("Helvetica", 10), relief="groove", bd=2,
                                      command=lambda opt=option: toggle_option_visibility(opt, all_options_list, canvas, fig, ax))
            toggle_button.grid(row=row, column=column, padx=10, pady=2, ipadx=10, ipady=5)
            row += 1


def main():
    root = tk.Tk()
    root.withdraw()  # Hide the root window while asking for input

    # Ask the user to select multiple image files
    image_paths = filedialog.askopenfilenames(title="Select images for processing",
                                              filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])

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


main()
