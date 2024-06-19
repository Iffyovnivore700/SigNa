from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.utils import mediainfo
import wave
import pyaudio
import time
import os

from io import BytesIO


app = Flask(__name__)

# Directory to store recorded WAV files
UPLOAD_FOLDER = 'C:\\Users\\carlo\\Downloads\\SigNa\\statics\\WAVsounds'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Define the path to the static and audio folders for text-to-speech (tts)
statics_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'statics')
audio_folder = os.path.join(statics_folder, 'audio')

# Ensure the audio folder exists (tts)
os.makedirs(audio_folder, exist_ok=True)

#Handle the recorder math#####
# Global variables for recording
RECORDING = False
RECORD_FILE = None
audio_frames = []

# Function to start recording
def start_recording(file_path):
    global RECORDING, RECORD_FILE, audio_frames

    if RECORDING:
        return

    RECORD_FILE = wave.open(file_path, 'wb')
    RECORD_FILE.setnchannels(1)
    RECORD_FILE.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
    RECORD_FILE.setframerate(44100)
    
    audio_frames = []
    RECORDING = True

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    frames_per_buffer=1024,
                    stream_callback=callback)

    stream.start_stream()
    return jsonify({'result': 'success'})

# Function to stop recording
def stop_recording():
    global RECORDING, RECORD_FILE, audio_frames

    if not RECORDING:
        return

    RECORDING = False
    RECORD_FILE.writeframes(b''.join(audio_frames))
    RECORD_FILE.close()

    audio_frames = []
    RECORD_FILE = None

    return jsonify({'result': 'success'})

# Callback function for audio stream
def callback(in_data, frame_count, time_info, status):
    global audio_frames

    if RECORDING:
        audio_frames.append(in_data)
        return in_data, pyaudio.paContinue
    else:
        return in_data, pyaudio.paComplete
######Finish recorder math#####

############################

# Serve static files (CSS, JavaScript, images)
app.static_folder = 'statics'
app.static_url_path = '/static'

#Handle the index
@app.route('/')
def index():
    return render_template('index.html')

#Handle the speech to text
@app.route('/speech-to-text.html')  # Define route for speech-to-text.html
def speech_to_text_page():
    return render_template('speech-to-text.html')

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    audio_file_path = 'C:\\Users\\carlo\\Downloads\\SigNa\\statics\\WAVsounds\\recording.wav'

    if not os.path.exists(audio_file_path):
        return jsonify({'error': 'Audio file not found'})

    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='es-ES')
            return jsonify({'transcription': text})
    except sr.UnknownValueError:
        return jsonify({'error': 'Unable to recognize speech'})
    except sr.RequestError:
        return jsonify({'error': 'Speech recognition service unavailable'})
    except Exception as e:
        return jsonify({'error': str(e)})

#Handle the recorder    
@app.route('/recorder.html')  # Define route for record.html
def record():
    return render_template('recorder.html')

@app.route('/recorder', methods=['GET', 'POST'])
def recorder():
    if request.method == 'POST':
        action = request.form['action']
        if action == 'start':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'recording.wav')
            return start_recording(file_path)
        elif action == 'stop':
            return stop_recording()

    return render_template('recorder.html')

#Handle the text input (tts)
@app.route('/text-input')
def text_input():
    return render_template('text_input.html')

#Perform Text-to-speech
@app.route('/convert', methods=['POST'])
def convert():
    if request.method == 'POST':
        text = request.form['text']
        language = 'es'
        mexicano = 'com.mx'

        tts = gTTS(text=text, lang=language, tld=mexicano, slow=False)
        
        # Generate a unique filename for each conversion
        audio_file = os.path.join(audio_folder, f'{hash(text)}.mp3')
        tts.save(audio_file)

        # Redirect to result page with the generated filename
        return redirect(url_for('audio_result', filename=f'{hash(text)}.mp3'))

#Handle the audio file (tts)
@app.route('/audio/<filename>')
def audio_result(filename):
    return render_template('tts_result.html', audio_file=url_for('static', filename=f'audio/{filename}'))



if __name__ == '__main__':
    app.run(debug=True)