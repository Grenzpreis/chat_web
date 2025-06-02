from flask import Flask, render_template, request
import os
from openai import OpenAI
from dotenv import load_dotenv
import tempfile
import base64

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    response = ""
    generated_image_url = ""
    uploaded_file_info = ""
    mode = "text"

    if request.method == "POST":
        user_input = request.form["user_input"]
        mode = request.form.get("mode", "text")
        uploaded_file = request.files.get("file")

        try:
            if mode == "text":
                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": user_input}]
                )
                response = completion.choices[0].message.content

            elif mode == "image":
                vision_description = ""
                if uploaded_file and uploaded_file.filename != "":
                    suffix = os.path.splitext(uploaded_file.filename)[1] or ".jpg"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp_path = tmp.name
                        uploaded_file.save(tmp_path)
                        uploaded_file_info = f"Hochgeladene Datei: {uploaded_file.filename} (temporär gespeichert)"

                    with open(tmp_path, "rb") as image_file:
                        image_bytes = image_file.read()
                        base64_image = base64.b64encode(image_bytes).decode("utf-8")
                        mime_type = uploaded_file.mimetype or "image/jpeg"
                        data_url = f"data:{mime_type};base64,{base64_image}"

                    vision_response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Beschreibe dieses Bild möglichst detailliert:"},
                                    {"type": "image_url", "image_url": {"url": data_url}}
                                ]
                            }
                        ]
                    )
                    vision_description = vision_response.choices[0].message.content.strip()
                    os.remove(tmp_path)

                full_prompt = f"{user_input}\n\nBildinhalt: {vision_description}" if vision_description else user_input

                image_response = client.images.generate(
                    model="dall-e-3",
                    prompt=full_prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                generated_image_url = image_response.data[0].url

        except Exception as e:
            response = f"Fehler: {e}"

    return render_template("index.html", response=response, image_url=generated_image_url,
                           uploaded_file_info=uploaded_file_info, mode=mode)

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)