from flask import Flask, request, render_template
from dotenv import load_dotenv
import os
import google.generativeai as genai
from PIL import Image
import io
import base64

# Load environment variables
load_dotenv()

# Configure Gemini AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Flask app
app = Flask(__name__)

# AI Prompt
input_prompt = """
You are an expert nutritionist. Look at the food items in the image and calculate the total calories. Provide the details of every food item with calorie intake in the following format:
1. Item 1 - no of calories
2. Item 2 - no of calories
- - - - -
"""

# Helper function to process the uploaded image
def input_image_setup(uploaded_file):
    if uploaded_file:
        # Read the image
        image = Image.open(uploaded_file)
        
        # Check if the image is in RGBA mode (with transparency), then convert to RGB
        if image.mode == "RGBA":
            image = image.convert("RGB")
        
        # Save to BytesIO object to pass to Gemini API
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="JPEG")
        
        # Return image data in the required format
        bytes_data = image_bytes.getvalue()
        image_parts = [
            {
                "mime_type": "image/jpeg",
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded.")

# Function to get response from Gemini API
def get_gemini_response(input, image, prompt):
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content((prompt, image[0], input))
    return response.text

# Landing page route
@app.route("/")
def landing_page():
    return render_template("index.html")

# Calculate page route
@app.route("/calculate", methods=["GET", "POST"])
def calculate_page():
    if request.method == "POST":
        input_text = request.form.get("input_prompt")
        uploaded_file = request.files.get("file")

        if uploaded_file:
            # Process image
            try:
                image_data = input_image_setup(uploaded_file)

                # Generate AI response
                response = get_gemini_response(input_prompt, image_data, input_text)
            except Exception as e:
                response = f"Error generating response: {e}"

            # Convert image to Base64 for rendering on the HTML page
            image = Image.open(uploaded_file)
            if image.mode == "RGBA":
                image = image.convert("RGB")
            image_bytes = io.BytesIO()
            image.save(image_bytes, format="JPEG")
            encoded_image = base64.b64encode(image_bytes.getvalue()).decode("utf-8")

            return render_template(
                "calculate.html",
                response=response,
                image_data=f"data:image/jpeg;base64,{encoded_image}"
            )
        else:
            return render_template(
                "calculate.html", error="Please upload an image file."
            )
    return render_template("calculate.html")

if __name__ == "__main__":
    app.run(debug=True)