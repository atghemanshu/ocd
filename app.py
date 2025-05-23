from flask import Flask, render_template, request, redirect, url_for
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document as DocxDocument
import os
import requests
import re 

app = Flask(__name__)

# OCR Space API Configuration (Remember to set your API key as environment variable in production!)
OCR_SPACE_API_URL = "https://api.ocr.space/parse/image"
OCR_SPACE_API_KEY = os.environ.get('OCR_SPACE_API_KEY')
if not OCR_SPACE_API_KEY:
    OCR_SPACE_API_KEY = "K87955728688957"
    print("Warning: Using hardcoded OCR Space API key. Use environment variables in production!")

# --- Add this Context Processor ---
@app.context_processor
def inject_utilities():
    """Injects utility functions into the template context."""
    return dict(get_database_data=get_database_data)
# ----------------------------------

def ocr_image_via_api(image_path):
    """Performs OCR on an image using OCR Space API."""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()

        payload = {
            'apikey': OCR_SPACE_API_KEY,
            'language': 'eng'
        }
        files = {'image': ('image.png', image_data)}

        response = requests.post(OCR_SPACE_API_URL, files=files, data=payload)
        response.raise_for_status()
        result = response.json()

        if result and not result.get('IsErroredOnProcessing'):
            text = result.get('ParsedResults')[0].get('ParsedText') if result.get('ParsedResults') else "No text found in image."
            return text.strip()
        else:
            error_message = result.get('ErrorMessage') or "Unknown error from OCR Space API."
            return f"OCR Space API Error: {error_message}"

    except requests.exceptions.RequestException as e:
        return f"Error connecting to OCR Space API: {e}"
    except Exception as e:
        return f"Error during OCR processing: {e}"


def extract_text_from_pdf(file_path):
    """Extracts text directly from a PDF file using pdfminer.six."""
    try:
        text = pdf_extract_text(file_path)
        return text.strip()
    except Exception as e:
        return f"Error extracting text from PDF: {e}"


def extract_text_from_docx(file_path):
    """Extracts text from a DOCX file using python-docx."""
    try:
        doc = DocxDocument(file_path)
        full_text = []
        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)
        return '\n'.join(full_text).strip() # Join paragraphs with newlines
    except Exception as e:
        return f"Error extracting text from DOCX: {e}"


def extract_text_from_file(file_path, filename):
    """Detects file type and calls appropriate extraction method."""
    file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    if file_extension in ['png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff']: # Image types
        return ocr_image_via_api(file_path)
    elif file_extension == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == 'docx':
        return extract_text_from_docx(file_path)
    else:
        return "Unsupported file format."

# --- NEW FUNCTIONS ---

def extract_structured_data(text):
    """Extracts specific structured data fields from text using regex."""
    data = {}
    # Define the fields we want to extract
    field_names = ["Sr no.", "Name", "City", "Age", "Country", "Address"]
    # Initialize all expected fields with None
    for field in field_names:
        data[field] = None

    lines = text.strip().split('\n')

    for field in field_names:
        # Create a regex pattern for each field:
        # - ^\s* : Start of the line with optional leading whitespace
        # - re.escape(field): The field name itself (escaped in case of special characters)
        # - \s*:\s*: Optional whitespace around the colon
        # - (.*) : Capture group for the value (everything after the colon)
        # - re.IGNORECASE: Make the matching case-insensitive
        pattern = re.compile(r"^\s*" + re.escape(field) + r"\s*:\s*(.*)", re.IGNORECASE)

        for line in lines:
            match = pattern.match(line.strip()) # Use match() to ensure it's at the beginning of the line
            if match:
                value = match.group(1).strip() # Get the captured group (the value) and strip whitespace
                # Store using the canonical field name from field_names
                data[field] = value
                break # Found this field, move to the next field_name

    return data
# Dummy database (replace with actual database in real application)
dummy_database = {
    "S001": {
        "Sr no.": "S001",
        "Name": "Hemanshu Kasar",
        "City": "Nagpur",
        "Age": "23",
        "Country": "India",
        "Address": "7, gurudeo nagar"
    },
    "S002": {
        "Sr no.": "S002",
        "Name": "John Doe",
        "City": "New York",
        "Age": "30",
        "Country": "USA",
        "Address": "123 Main St"
    },
    "S003": {
        "Sr no.": "S003",
        "Name": "Sarah Johnson",
        "City": "London",
        "Age": "27",
        "Country": "UK",
        "Address": "45 Oxford Street"
    },
    "S004": {
        "Sr no.": "S004",
        "Name": "Raj Patel",
        "City": "Mumbai",
        "Age": "32",
        "Country": "India",
        "Address": "201, Sea View Apartments"
    },
    "S005": {
        "Sr no.": "S005",
        "Name": "Maria Garcia",
        "City": "Barcelona",
        "Age": "29",
        "Country": "Spain",
        "Address": "Carrer de Mallorca, 15"
    },
    "S006": {
        "Sr no.": "S006",
        "Name": "Akira Tanaka",
        "City": "Tokyo",
        "Age": "35",
        "Country": "Japan",
        "Address": "2-1-3 Shibuya"
    },
    "S007": {
        "Sr no.": "S007",
        "Name": "Chen Wei",
        "City": "Shanghai",
        "Age": "26",
        "Country": "China",
        "Address": "88 Nanjing Road"
    },
    "S008": {
        "Sr no.": "S008",
        "Name": "Lucas Silva",
        "City": "São Paulo",
        "Age": "31",
        "Country": "Brazil",
        "Address": "Rua Augusta, 1200"
    },
    "S009": {
        "Sr no.": "S009",
        "Name": "Olivia Miller",
        "City": "Sydney",
        "Age": "28",
        "Country": "Australia",
        "Address": "42 Bondi Beach Road"
    },
    "S010": {
        "Sr no.": "S010",
        "Name": "Ahmed Hassan",
        "City": "Cairo",
        "Age": "33",
        "Country": "Egypt",
        "Address": "17 Al Tahrir Square"
    }
}


def get_database_data(sr_no):
    """Fetches data from the dummy database based on Sr no."""
    return dummy_database.get(sr_no, None) # Returns None if Sr no. not found


def compare_data(extracted_data, db_data):
    """Compares extracted data with database data and calculates accuracy."""
    if not db_data:
        return 0, {}, "Sr no. not found in database." # Return error message if no db data

    matched_fields = 0
    mismatched_fields = {}
    total_fields = len(db_data) # Assuming db_data has all expected fields

    for key, db_value in db_data.items():
        extracted_value = extracted_data.get(key) # Get extracted value, might be None
        if extracted_value == db_value:
            matched_fields += 1
        else:
            mismatched_fields[key] = {"db_value": db_value, "extracted_value": extracted_value}

    accuracy = (matched_fields / total_fields) * 100 if total_fields > 0 else 0
    return accuracy, mismatched_fields, None # No error message if comparison successful


@app.route('/', methods=['GET', 'POST'])
def index():
    results = {}

    if request.method == 'POST':
        if 'image' not in request.files:
            return "No file part"

        image_files = request.files.getlist('image')

        for image_file in image_files:
            filename = image_file.filename
            if filename == '':
                results[filename] = {"error": "No selected file"} # Store error in results
                continue

            if image_file:
                temp_file_path = "temp_file"
                file_extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else '' # Corrected extension extraction
                temp_file_path = f"{temp_file_path}.{file_extension}"

                image_file.save(temp_file_path)
                extracted_text = extract_text_from_file(temp_file_path, filename)
                structured_data = {} # Initialize
                accuracy = None
                mismatched_fields = {}
                comparison_error = None

                if extracted_text and not extracted_text.startswith("Error"): # Proceed only if text extraction was successful
                    if file_extension in ['docx', 'pdf','png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff']: # Only process structured data for DOCX for now (can extend to images/PDFs later)
                        structured_data = extract_structured_data(extracted_text)
                        sr_no_value = structured_data.get("Sr no.") # Assuming "Sr no." is the key to database
                        if sr_no_value:
                            db_data = get_database_data(sr_no_value)
                            accuracy, mismatched_fields, comparison_error = compare_data(structured_data, db_data)
                        else:
                            comparison_error = "Sr no. not found in extracted data, cannot compare."

                results[filename] = {
                    "extracted_text": extracted_text,
                    "structured_data": structured_data,
                    "accuracy": accuracy,
                    "mismatched_fields": mismatched_fields,
                    "comparison_error": comparison_error
                }
                os.remove(temp_file_path)

    return render_template('index.html', results=results)


if __name__ == '__main__':
    app.run(debug=True)