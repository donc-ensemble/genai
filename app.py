import os
import base64
from flask import Flask, request, jsonify, render_template
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def encode_image64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def get_media_type(file_extension):
    if file_extension == ".png":
        return "image/png"
    elif file_extension == ".jpg" or file_extension == ".jpeg":
        return "image/jpeg"
    elif file_extension == ".webp":
        return "image/webp"
    else:
        raise ValueError("Unsupported image format. Please use PNG, JPG, or WebP.")

def analyze_image(image_path, user_prompt):
    base_prompt = (
        "Generate CSS and HTML based on the image provided. "
        "Use a placeholder if an image is needed from https://picsum.photos/. "
        "Strictly do not add any comments to the code."
        "All the code must be generated, no shortcuts. "
        '''
            <!DOCTYPE html>
        <html lang="en">
        <head>`
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <style>
                The CSS must go here
            </style>
        </head>
        <body>
            The html body has to go here
            <script>
            Related javascript goes here if there is any
            </script>
        </body>
        </html>
        '''
    )

    full_prompt = f"{base_prompt} {user_prompt}"

    base64_image = encode_image64(image_path)
    image_media_type = get_media_type(os.path.splitext(image_path)[1].lower())
    
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        temperature=0,
        max_tokens=4096, #original is 1024, I increased it to 4096 to handle larger responses
        system="You are an expert in HTML, CSS, and JavaScript and UI.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_media_type,
                            "data": base64_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": full_prompt
                    }
                ],
            }
        ],
    )
    return message.content[0].text

# Flask routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    try:
        image = request.files["image"]
        query = request.form["query"]

        image_path = os.path.join("uploads", image.filename)
        image.save(image_path)

        response = analyze_image(image_path, query)
        print(response)
        os.remove(image_path)

        return jsonify({"success": True, "html": response})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    if not os.path.exists("uploads"):
        os.mkdir("uploads")
    app.run(debug=True)