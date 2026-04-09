import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 🔇 hide tensorflow warnings

from flask import Response
from flask import Flask, render_template, jsonify
import cv2
from deepface import DeepFace
import speech_recognition as sr
from textblob import TextBlob
import threading
import pyttsx3

def generate_frames():
    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            

app = Flask(__name__)


def generate_emotion_frames():
    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        try:
            # analyze emotion
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            emotions = result[0]['emotion']

            # get dominant emotion
            dominant = max(emotions, key=emotions.get)

            # draw text on frame
            cv2.putText(frame, dominant, (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 255, 0), 2, cv2.LINE_AA)

        except:
            pass

        # convert frame to jpg
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# ==============================
# 🔊 SAFE TEXT-TO-SPEECH (FIXED)
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
# 💡 RECOMMENDATION SYSTEM
# ==============================
def get_recommendation(emotion):
    return {
        "happy": "Keep smiling 😊",
        "sad": "Take a break and relax",
        "stressed": "Try meditation 🧘",
        "surprised": "Unexpected moment 😲",
        "angry": "Calm down and breathe",
        "neutral": "Stay focused 👍"
    }.get(emotion, "Stay balanced")


# ==============================
# 🏠 HOME
# ==============================
@app.route('/')
def index():
    return render_template('index.html')


# ==============================
# 😃 FACE EMOTION (FIXED)
# ==============================
@app.route('/detect_emotion')
def detect_emotion():
    try:
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            return jsonify({"error": "Camera not accessible"})

        ret, frame = cap.read()
        cap.release()
        cv2.destroyAllWindows()

        if not ret:
            return jsonify({"error": "Failed to capture image"})

        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)

        emotions = result[0]['emotion']

        # convert float32 → float
        clean = {k: float(v) for k, v in emotions.items()}

        # 🔥 IMPROVED DETECTION LOGIC
        if clean["angry"] > 35:
            dominant = "angry"
        elif clean["sad"] > 35:
            dominant = "sad"
        elif clean["surprise"] > 25:
            dominant = "surprised"
        elif clean["happy"] > 35:
            dominant = "happy"
        elif clean["fear"] > 25:
            dominant = "stressed"
        else:
            dominant = "neutral"

        suggestion = get_recommendation(dominant)

        # 🔊 SPEAK OUTPUT
        speak(f"You are {dominant}")

        return jsonify({
            "emotion": dominant,
            "suggestion": suggestion
        })

    except Exception as e:
        return jsonify({"error": str(e)})



@app.route('/emotion_video_feed')
def emotion_video_feed():
    return Response(generate_emotion_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')




# ==============================
# 🎤 VOICE EMOTION (FIXED)
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

        polarity = float(TextBlob(text).sentiment.polarity)

        # 🔥 STRONG LOGIC
        if any(w in t for w in ["happy", "great", "awesome", "good"]):
            emotion = "happy"
        elif any(w in t for w in ["sad", "bad", "upset"]):
            emotion = "sad"
        elif any(w in t for w in ["angry", "mad"]):
            emotion = "angry"
        elif any(w in t for w in ["stress", "tired"]):
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

        suggestion = get_recommendation(emotion)

        # 🔊 SPEAK OUTPUT
        speak(f"You said {text}. Emotion detected is {emotion}")

        return jsonify({
            "emotion": emotion,
            "text": text,
            "suggestion": suggestion
        })

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
# ==============================
# 🚀 RUN APP
# ==============================
if __name__ == '__main__':
    app.run(debug=True)