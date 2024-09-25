# Course Schedule OCR Application

This project is a course scheduling application that reads course schedules from images (in Hebrew), processes them using OCR, and displays the courses in a graphical weekly schedule format. It allows users to visualize their courses, manage multiple schedules, and toggle course visibility.

## Features

- Extracts course information from images using OCR.
- Displays course schedules in a graphical calendar format.
- Allows toggling course visibility on the schedule.
- Supports multiple images and displays them in one calendar.
- Designed with a modern interface inspired by Google Calendar/iPhone schedules.

## Installation

Ensure that you have Python 3.x installed. Then, install the required dependencies using:
pip install -r requirements.txt

## Install Tesseract OCR
The project requires Tesseract OCR to process the images. Follow the installation instructions for your platform:

Windows
Download the installer from the official Tesseract GitHub page.

Linux (Debian/Ubuntu)
sudo apt install tesseract-ocr

macOS
brew install tesseract

## Usage
Once dependencies and Tesseract are installed, you can run the program with the following command:
python main.py

## Steps to Use:
The program will prompt you to select image files containing your course schedule.
You'll be asked to input titles for each image.
The schedule will be displayed with an option to toggle course visibility.

### Clone the Repository

```bash
git clone https://github.com/yourusername/course-schedule.git
cd your-repository-name


