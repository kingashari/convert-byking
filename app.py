from flask import Flask, render_template, request, send_from_directory, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import subprocess

app = Flask(__name__)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER


def allowed_file(filename):
    """Check if the uploaded file is allowed based on its extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_to_purestatus_format(input_file, output_file):
    """
    Convert a video file to PureStatus-like format (MP4 with H.264, reduced bitrate and resolution).
    """
    try:
        command = [
            "ffmpeg",
            "-i", input_file,
            "-vf", "scale=1080:1920",  # Resize to 1080x1920 (portrait)
            "-r", "29.97",            # Set frame rate to 29.97 FPS
            "-b:v", "4M",             # Set video bitrate to 4 Mbps
            "-c:v", "libx264",        # Use H.264 codec for video
            "-preset", "fast",        # Use fast preset for encoding
            "-c:a", "aac",            # Use AAC codec for audio
            "-b:a", "128k",           # Set audio bitrate to 128 kbps
            "-strict", "experimental",
            output_file
        ]
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print("Error during conversion:", e)
        raise
    except Exception as e:
        print("Unexpected error:", e)
        raise


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    # Proses upload file
    if 'input_file' not in request.files:
        flash("No file uploaded", "danger")
        return redirect(url_for('index'))

    file = request.files['input_file']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash("Invalid file type. Only allowed: mp4, avi, mov, mkv.", "danger")
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    output_filename = f"converted_{filename.rsplit('.', 1)[0]}.mp4"
    output_path = os.path.join(app.config['CONVERTED_FOLDER'], output_filename)

    # Save file
    file.save(input_path)

    # Proses konversi video
    try:
        convert_to_purestatus_format(input_path, output_path)
        flash("File converted successfully!", "success")
    except Exception as e:
        flash(f"File conversion failed: {str(e)}", "danger")

    return render_template('index.html', message="File converted successfully!", converted_file=output_filename)


@app.route('/download/<filename>')
def download(filename):
    """Serve converted files."""
    return send_from_directory(app.config['CONVERTED_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
