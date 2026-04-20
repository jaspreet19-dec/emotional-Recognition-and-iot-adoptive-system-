import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from flask import Flask, render_template, jsonify, request, redirect, session, Response 
import sqlite3
import cv2
from deepface import DeepFace
import speech_recognition as sr
from textblob import TextBlob
import threading
import pyttsx3
from collections import Counter
import numpy as np

app = Flask(__name__)
app.secret_key = "secret123"

# ==============================
# 🔊 TEXT TO SPEECH
# ==============================
def speak(text):
    def run():
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except:
            pass
    threading.Thread(target=run).start()

# ==============================
# 💡 RECOMMENDATION
# ==============================
def get_recommendation(emotion):
    return {
        "happy": "Keep smiling 😊",
        "sad": "Take a break",
        "stressed": "Relax 🧘",
        "surprised": "Unexpected 😲",
        "angry": "Calm down",
        "neutral": "Stay focused"
    }.get(emotion, "Stay balanced")

# ==============================
# 🧾 DATABASE
# ==============================
def init_db():
    conn = sqlite3.connect("users.db")
    conn.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT)")
    conn.close()

init_db()

# ==============================
# 🔐 LOGIN SYSTEM
# ==============================
@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        conn = sqlite3.connect("users.db")
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p)).fetchone()
        conn.close()

        if user:
            session['user'] = u
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid Credentials")

    return render_template('login.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        conn = sqlite3.connect("users.db")
        conn.execute("INSERT INTO users VALUES (?,?)", (u,p))
        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template('dashboard.html')

# ==============================
# 🎥 FACE DETECTOR (FAST)
# ==============================
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# ==============================
# 🎥 LIVE VIDEO (FAST + ACCURATE)
# ==============================
def generate_frames():
    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face = frame[y:y+h, x:x+w]

            try:
                result = DeepFace.analyze(
                    face,
                    actions=['emotion'],
                    detector_backend='opencv',
                    enforce_detection=False
                )

                emotions = result[0]['emotion']
                dominant = max(emotions, key=emotions.get)
                confidence = emotions[dominant]

                if confidence > 50:
                    text = f"{dominant} ({int(confidence)}%)"
                else:
                    text = "Detecting..."

                cv2.putText(frame, text, (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                            (0, 255, 0), 2)

                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

            except:
                pass

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# ==============================
# 😃 FACE EMOTION (FAST + STABLE)
# ==============================
@app.route('/detect_emotion')
def detect_emotion():
    try:
        cap = cv2.VideoCapture(0)
        emotions_list = []

        for i in range(5):  # 🔥 faster
            ret, frame = cap.read()
            if not ret:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 0:
                continue

            for (x, y, w, h) in faces:
                face = frame[y:y+h, x:x+w]

                try:
                    result = DeepFace.analyze(
                        face,
                        actions=['emotion'],
                        detector_backend='opencv',
                        enforce_detection=False
                    )

                    emotions = result[0]['emotion']
                    dominant = max(emotions, key=emotions.get)

                    if emotions[dominant] > 50:
                        emotions_list.append(dominant)

                except:
                    continue

        cap.release()

        if not emotions_list:
            return jsonify({"error": "Face not clear"})

        final = Counter(emotions_list).most_common(1)[0][0]

        speak(f"You are {final}")

        return jsonify({
            "emotion": final,
            "suggestion": get_recommendation(final)
        })

    except Exception as e:
        return jsonify({"error": str(e)})

# ==============================
# 🎤 VOICE EMOTION (IMPROVED)
# ==============================
@app.route('/voice_emotion')
def voice_emotion():
    try:
        r = sr.Recognizer()

        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=5, phrase_time_limit=5)

        text = r.recognize_google(audio)
        t = text.lower()

        polarity = TextBlob(text).sentiment.polarity

        # 🔥 SMART DETECTION
        if any(w in t for w in ["happy", "great", "awesome", "good", "nice"]):
            emotion = "happy"

        elif any(w in t for w in ["sad", "bad", "upset", "depressed"]):
            emotion = "sad"

        elif any(w in t for w in ["angry", "mad", "furious"]):
            emotion = "angry"

        elif any(w in t for w in ["stress", "tired", "pressure"]):
            emotion = "stressed"

        elif any(w in t for w in ["wow", "amazing", "surprise"]):
            emotion = "surprised"

        else:
            if polarity > 0.3:
                emotion = "happy"
            elif polarity < -0.3:
                emotion = "sad"
            else:
                emotion = "neutral"

        speak(f"You said {text}. Emotion is {emotion}")

        return jsonify({
            "emotion": emotion,
            "suggestion": get_recommendation(emotion)
        })

    except Exception as e:
        return jsonify({"error": str(e)})

# ==============================
# 🚀 RUN
# ==============================
if __name__ == '__main__':
    app.run(debug=True)