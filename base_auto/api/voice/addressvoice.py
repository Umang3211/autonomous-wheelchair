import speech_recognition as sr

r = sr.Recognizer()

def take_address():
    with sr.Microphone() as source:
        # print("Say smthn")
        audio = r.listen(source)

    try: 
        text = r.recognize_google(audio)
        return text
        # print("you said: {}".format(text))
    except sr.UnknownValueError:
        print(f"Do not understand what you r saying")
    except sr.RecquestError as e:
        print(f"Could not request results from google speech recog services")