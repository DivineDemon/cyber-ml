import os
import random
from flask import Flask, render_template, request, session
import requests
import joblib
from sklearn.preprocessing import LabelEncoder
import pandas as pd
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET")

#====================#
#| Helper Functions |#
#====================#


# OTP Generator Helper Function
def generateOTP():
    return random.randrange(10000, 99999)


# OTP API Helper Function
def getOTPApi(phone):
    account_sid = os.getenv("TWILIO_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    otp = generateOTP()
    session['response'] = str(otp)
    client = Client(account_sid, auth_token)
    message = client.messages.create(to=phone,
                                     from_="+19793664234",
                                     body="Your OTP is: " + str(otp))

    if message.sid:
        return True
    else:
        False


# Get Client IP Address
def client_ip():
    ip = request.remote_addr
    return ip


# Get Client Country
def client_country():
    ip = client_ip()
    response = requests.get("http://ip-api.com/json/{}".format(ip))
    js = response.json()
    country = js['countryCode']
    if country:
        return country
    else:
        return "User IP Not Accessible!"


# Import Model and Predict
def model():
    # Loading ML Model
    model = joblib.load('./model/model.joblib')

    # Getting Client IP
    ip = client_ip()

    # Getting Client Country
    country = client_country()

    # Creating DataFrame for ML Model
    x = {'IP': [ip], 'Country': [country]}
    user_info = pd.DataFrame(x)
    categ = ['IP', 'Country']

    # Encoding DataFrame
    le = LabelEncoder()
    user_info[categ] = user_info[categ].apply(le.fit_transform)

    # Fitting Model
    prediction = model.predict(user_info)

    # Writing Prediction Result in a .txt File
    prediction_file = open("prediction_file.txt", "a")
    prediction_file.write("\n")
    prediction_file.write(str(prediction))

    # Returning Prediction Result
    return prediction[0]


#==========#
#| Routes |#
#==========#


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/getOTP", methods=['POST'])
def getOTP():
    phone = request.form['phone']
    check = getOTPApi(phone)
    if check:
        return render_template("enterOTP.html")


@app.route("/validateOTP", methods=['POST'])
def validateOTP():
    otp = request.form['otp']
    model_check = model()
    if 'response' in session:
        s = session['response']
        session.pop('response', None)
        if s == otp and model_check == 'normal':
            return 'Successful Login!'
        else:
            return 'Anomaly IP Detected, Please Retry Login!'


if __name__ == "__main__":
    app.run(debug=True, port=3000)
