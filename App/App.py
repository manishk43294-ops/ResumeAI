# Developed by manishk43294-ops    Made with Streamlit

###### Packages Used ######
import streamlit as st
import pandas as pd
import base64
import random
import time
import datetime
import pymysql
import os
import socket
import platform
import geocoder
import secrets
import io
import plotly.express as px
from geopy.geocoders import Nominatim
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos

###### Helpers ######

def inject_custom_css(theme="Light"):
    if theme == "Dark":
        css = '''
        <style>
            .stApp { background-color: #0b1120; color: #e2e8f0; }
            .css-1d391kg, .css-1d391kg p, .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 { color: #e2e8f0; }
            .stButton>button { background-color: #1e293b; color: #e2e8f0; }
        </style>
        '''
    else:
        css = '''
        <style>
            .stApp { background-color: #ffffff; color: #020617; }
        </style>
        '''
    st.markdown(css, unsafe_allow_html=True)


def get_csv_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'


def pdf_reader(file_path):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file_path, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
        text = fake_file_handle.getvalue()
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, 'rb') as f:
        pdf_bytes = f.read()
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    iframe = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="900" type="application/pdf"></iframe>'
    st.markdown(iframe, unsafe_allow_html=True)


def course_recommender(course_list):
    st.subheader('Courses & certificates recommendations')
    count = st.slider('How many recommendations?', 1, 10, 5)
    random.shuffle(course_list)
    for idx, (title, link) in enumerate(course_list[:count], start=1):
        st.markdown(f'{idx}. [{title}]({link})')
    return [title for title, _ in course_list[:count]]


def connect_database():
    return pymysql.connect(host='localhost', user='root', password='root@MySQL4admin', db='cv', charset='utf8mb4')


def ensure_tables(conn):
    cursor = conn.cursor()
    cursor.execute('CREATE DATABASE IF NOT EXISTS CV;')
    cursor.execute('USE CV;')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS user_data (
            ID INT NOT NULL AUTO_INCREMENT,
            sec_token VARCHAR(50),
            ip_add VARCHAR(50),
            host_name VARCHAR(100),
            dev_user VARCHAR(100),
            os_name_ver VARCHAR(100),
            latlong VARCHAR(100),
            city VARCHAR(100),
            state VARCHAR(100),
            country VARCHAR(100),
            act_name VARCHAR(100),
            act_mail VARCHAR(100),
            act_mob VARCHAR(50),
            Name VARCHAR(500),
            Email_ID VARCHAR(500),
            resume_score VARCHAR(20),
            Timestamp VARCHAR(50),
            Page_no VARCHAR(10),
            Predicted_Field TEXT,
            User_level TEXT,
            Actual_skills TEXT,
            Recommended_skills TEXT,
            Recommended_courses TEXT,
            pdf_name VARCHAR(200),
            PRIMARY KEY (ID)
        )''')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS user_feedback (
            ID INT NOT NULL AUTO_INCREMENT,
            feed_name VARCHAR(100),
            feed_email VARCHAR(200),
            feed_score VARCHAR(10),
            comments TEXT,
            Timestamp VARCHAR(50),
            PRIMARY KEY (ID)
        )''')
    conn.commit()
    return conn


def insert_data(conn, values):
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO user_data (
            sec_token, ip_add, host_name, dev_user, os_name_ver, latlong, city, state, country,
            act_name, act_mail, act_mob, Name, Email_ID, resume_score, Timestamp, Page_no,
            Predicted_Field, User_level, Actual_skills, Recommended_skills, Recommended_courses, pdf_name
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
        values)
    conn.commit()


def insert_feedback(conn, name, email, score, comments, timestamp):
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO user_feedback (feed_name, feed_email, feed_score, comments, Timestamp) VALUES (%s, %s, %s, %s, %s)',
        (name, email, score, comments, timestamp))
    conn.commit()


def detect_experience_level(text):
    text_upper = text.upper()
    if 'EXPERIENCE' in text_upper or 'WORK EXPERIENCE' in text_upper:
        return 'Experienced'
    if 'INTERNSHIP' in text_upper or 'INTERNSHIPS' in text_upper:
        return 'Intermediate'
    return 'Fresher'


def classify_field(skills):
    keywords = {
        'Data Science': ['tensorflow', 'keras', 'pytorch', 'scikit', 'machine learning', 'data science', 'pandas'],
        'Web Development': ['django', 'flask', 'react', 'node', 'javascript', 'html', 'css'],
        'Android Development': ['android', 'kotlin', 'flutter', 'java', 'xml'],
        'IOS Development': ['ios', 'swift', 'xcode', 'objective-c'],
        'UI-UX Design': ['figma', 'adobe xd', 'ux', 'ui', 'prototyping']
    }
    for field, keys in keywords.items():
        for skill in skills:
            for keyword in keys:
                if keyword.lower() in str(skill).lower():
                    return field
    return 'General'


def show_user_page(conn):
    st.header('Upload Your Resume')
    name = st.text_input('Name')
    email = st.text_input('Email')
    phone = st.text_input('Phone')
    resume_file = st.file_uploader('Upload PDF resume', type=['pdf'])
    if resume_file is not None:
        upload_path = './Uploaded_Resumes/' + resume_file.name
        with open(upload_path, 'wb') as f:
            f.write(resume_file.getbuffer())
        show_pdf(upload_path)
        with st.spinner('Parsing resume...'):
            resume_data = ResumeParser(upload_path).get_extracted_data()
        if resume_data:
            resume_text = pdf_reader(upload_path)
            st.subheader('Parsed Resume Data')
            st.write({
                'Name': resume_data.get('name'),
                'Email': resume_data.get('email'),
                'Mobile': resume_data.get('mobile_number'),
                'Degree': resume_data.get('degree'),
                'Pages': resume_data.get('no_of_pages'),
                'Skills': resume_data.get('skills')
            })
            field = classify_field(resume_data.get('skills') or [])
            st.success(f'Recommended field: {field}')
            level = detect_experience_level(resume_text)
            st.info(f'Estimated experience level: {level}')
            courses = []
            if field == 'Data Science':
                courses = course_recommender(ds_course)
            elif field == 'Web Development':
                courses = course_recommender(web_course)
            elif field == 'Android Development':
                courses = course_recommender(android_course)
            elif field == 'IOS Development':
                courses = course_recommender(ios_course)
            elif field == 'UI-UX Design':
                courses = course_recommender(uiux_course)
            else:
                st.write('No targeted course recommendations available for this field yet.')
            ts = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
            values = (
                secrets.token_urlsafe(12), socket.gethostbyname(socket.gethostname()), socket.gethostname(), os.getlogin(),
                platform.system() + ' ' + platform.release(), None, None, None, None,
                name, email, phone, resume_data.get('name'), resume_data.get('email'), str(0), ts,
                str(resume_data.get('no_of_pages') or 0), field, level, str(resume_data.get('skills') or []), str([]), str(courses), resume_file.name
            )
            insert_data(conn, values)
            st.balloons()
        else:
            st.error('Unable to parse the resume. Please check the PDF file and try again.')


def show_feedback_page(conn):
    st.header('Feedback')
    with st.form('feedback_form'):
        name = st.text_input('Name')
        email = st.text_input('Email')
        score = st.slider('Rate the tool', 1, 5, 3)
        comments = st.text_area('Comments')
        submitted = st.form_submit_button('Submit')
        if submitted:
            ts = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
            insert_feedback(conn, name, email, score, comments, ts)
            st.success('Thank you! Your feedback has been saved.')
    feedback = pd.read_sql('SELECT * FROM user_feedback', conn)
    if not feedback.empty:
        st.write(feedback)
        st.markdown(get_csv_download_link(feedback, 'feedback.csv', 'Download feedback data'), unsafe_allow_html=True)


def show_about_page():
    st.header('About AI Resume Analyzer')
    st.write('This resume analyzer app parses your uploaded PDF resume and provides skill recommendations and a suggested career field.')
    st.write('It is now maintained by manishk43294-ops.')


def show_admin_page(conn):
    st.header('Admin Dashboard')
    username = st.text_input('Admin username')
    password = st.text_input('Admin password', type='password')
    if st.button('Login'):
        if username == 'admin' and password == 'admin@resume-analyzer':
            data = pd.read_sql('SELECT * FROM user_data', conn)
            feedback = pd.read_sql('SELECT * FROM user_feedback', conn)
            st.subheader('User submissions')
            st.write(data)
            st.markdown(get_csv_download_link(data, 'user_data.csv', 'Download user data'), unsafe_allow_html=True)
            st.subheader('Feedback')
            st.write(feedback)
        else:
            st.error('Invalid admin credentials')


def main():
    st.set_page_config(page_title='AI Resume Analyzer', page_icon='./Logo/recommend.png')
    theme = st.sidebar.radio('Theme', ['Light', 'Dark'], index=0)
    inject_custom_css(theme)
    st.sidebar.markdown('## Navigation')
    if 'page' not in st.session_state:
        st.session_state.page = 'User'
    for page in ['User', 'Feedback', 'About', 'Admin']:
        if st.sidebar.button(page):
            st.session_state.page = page
    st.sidebar.markdown('<b>Built by <a href="https://github.com/manishk43294-ops">manishk43294-ops</a></b>', unsafe_allow_html=True)
    conn = connect_database()
    conn = ensure_tables(conn)
    if st.session_state.page == 'User':
        show_user_page(conn)
    elif st.session_state.page == 'Feedback':
        show_feedback_page(conn)
    elif st.session_state.page == 'About':
        show_about_page()
    else:
        show_admin_page(conn)

if __name__ == '__main__':
    main()
