from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, TextAreaField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired
import fitz
from transformers import pipeline

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/files'

class UploadFileForm(FlaskForm):
    file = FileField("File")
    submit = SubmitField("Upload ")

class UploadTextForm(FlaskForm):
    text = TextAreaField('Which actor is your favorite?', validators=[InputRequired()],default="0")
    tsubmit = SubmitField("Upload")

final_summary=None
@app.route('/', methods=['GET',"POST"])
@app.route('/home', methods=['GET',"POST"])
def home():
    form = UploadFileForm()
    tform = UploadTextForm()

    if tform.validate_on_submit():
        text=preprocess(tform.text.data)
        final_summary=summarize(text)
        return render_template('index.html',tform=tform, form=form, summary=final_summary,blankspace="      ")
    
    elif form.validate_on_submit():
        file = form.file.data # First grab the file
        file_name = secure_filename(file.filename)
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))) # Then save the file
        
        pdf_path="static/files/"+file_name

        text_from_pdf=extract_text_from_pdf(pdf_path)
        text_from_pdf=preprocess(text_from_pdf)
        
        final_summary=summarize(text_from_pdf)
        os.remove(pdf_path)

        return render_template('index.html',tform=tform, form=form, summary=final_summary,blankspace="      ")

    return render_template('index.html',tform=tform, form=form,summary="Notes will be displayed here",blankspace="      ")

def extract_text_from_pdf(pdf_path):
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    text = ""
    # Iterate through each page
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)  # Load each page
        text += page.get_text()  # Extract text from the page
    return text

def summarize(to_summarize):
    summarizer=pipeline("summarization",model='t5-base',tokenizer='t5-base',framework='pt')
    summary = summarizer(to_summarize,max_length=100,min_length=10,do_sample=False)
    final_summary=summary[0]['summary_text']
    return final_summary

def preprocess(text):
    return text
if __name__ == '__main__':
    app.run(debug=True)
