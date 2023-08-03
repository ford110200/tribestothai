from flask import Flask, render_template, request, redirect,url_for,session ,g , jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask import flash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
import speech_recognition as sr


import os
import sqlite3


app = Flask(__name__,template_folder='templates')
app.secret_key = '1102001235'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///questions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_LESSON'] = 'static/upload_lessons'
Session(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    image = db.Column(db.String(100))
    lesson = db.Column(db.Integer , nullable=False)


    def __repr__(self):
        return f"Question(question='{self.question}', image='{self.image}' lesson ='{self.lesson} "

class submit_report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(500), nullable=False)
    problem = db.Column(db.String(500), nullable=False)
    email = db.Column(db.String(500), nullable=False)
    image = db.Column(db.String(100))
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"User(username='{self.username}', password='{self.password}', name='{self.name}', surname='{self.surname}', age={self.age}, role='{self.role}')"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif', 'mp3'}



class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.Text, nullable=False)
    sound_filename_thai = db.Column(db.Text, nullable=False)
    sound_filename_hmong_daw = db.Column(db.Text, nullable=False)
    sound_filename_hmong_njua = db.Column(db.Text, nullable=False)
    sound_filename_lahu = db.Column(db.Text, nullable=False)
    sound_filename_lisu = db.Column(db.Text, nullable=False)
    sound_filename_arka = db.Column(db.Text, nullable=False)
    sound_filename_karen = db.Column(db.Text, nullable=False)
    lesson_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Lesson(title='{self.title}', image_filename='{self.image_filename}', sound_filename_thai='{self.sound_filename_thai}', sound_filename_hmong_daw='{self.sound_filename_hmong_daw}', sound_filename_hmong_njua='{self.sound_filename_hmong_njua}', sound_filename_lahu='{self.sound_filename_lahu}', sound_filename_lisu='{self.sound_filename_lisu}', sound_filename_arka='{self.sound_filename_arka}',sound_filename_karen='{self.sound_filename_karen}', lesson_id={self.lesson_id})"

def create_tables():
    with app.app_context():
        db.create_all()
def get_lessons(lesson_id):
    connection = sqlite3.connect('instance/questions.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM lesson WHERE lesson_id = ?', (lesson_id,))
    lessons = cursor.fetchall()
    connection.close()
    return lessons


DATABASE = os.path.join(app.instance_path, 'questions.db')  # Update the path accordingly

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.execute('PRAGMA foreign_keys = ON')
    return db

def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/contact_page', methods=['GET'])
def contact_page():
    return render_template('contact_page.html')



@app.route('/submit_form', methods=['POST'])
def submit_form():
    username = request.form['username']
    problem = request.form['problem']
    email = request.form['email']
    image = request.files['image']

    image.save('static/report/' + image.filename)

    import sqlite3
    conn = sqlite3.connect('instance/questions.db')
    cursor = conn.cursor()

    cursor.execute("INSERT INTO submit_report (username, problem, email, image) VALUES (?, ?, ?, ?)",
                   (username, problem, email, '/report/' + image.filename))

    conn.commit()
    conn.close()

    return "ข้อมูลที่ได้รับคือ: ชื่อผู้ใช้ - {}, ปัญหาที่พบ - {}, อีเมล - {}".format(username, problem, email)

@app.route('/admin_report', methods=['GET'])
def admin_report():
    submit_reports = get_all_submit()
    return render_template('admin_report.html' , submit_reports=submit_reports)


@app.route('/lesson_pic')
def lesson_pic():
    return render_template('lesson_pic.html')

@app.route('/student_dashboard')
def student_dashboard():
    if 'username' in session:
        return render_template('student_dashboard.html')
    else:
        return redirect(url_for('student_login'))



@app.route('/lesson_select')
def lesson_select():
    return render_template('lesson_select.html')

@app.route('/quiz_select')
def quiz_select():
    return render_template('quiz_select.html')

def transform_path(path):
    path_parts = path.split('/')

    if path_parts[0] == 'static':
        path_parts.pop(0)

    new_path = '/'.join(path_parts)

    return new_path


@app.route('/quiz_result')
def quiz_result():
    return render_template("quiz_result.html")


@app.route('/question/<int:lesson>')
def display_quiz(lesson):
    quiz_questions = Question.query.filter_by(lesson=lesson).all()
    if quiz_questions:
        for question in quiz_questions:
            question.image = transform_path(question.image)

        return render_template('quiz.html', questions=quiz_questions)
    else:
        return "Quiz not found"


def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("กรุณาพูดคำถามของคุณ...")
        audio = recognizer.listen(source)

    try:
        print("กำลังแปลงเสียงเป็นข้อความ...")
        question_text = recognizer.recognize_google(audio, language='th')
        print(f"ข้อความที่ได้คือ: {question_text}")
        return question_text
    except sr.UnknownValueError:
        print("ไม่สามารถรับรู้เสียงที่พูดได้")
        return None
    except sr.RequestError:
        print("ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ Google")
        return None


@app.route('/lesson/<int:lesson_id>')
def display_lesson(lesson_id):
    # ใช้ SQLAlchemy query เพื่อดึงข้อมูลของบทเรียนที่ต้องการจากฐานข้อมูล
    lesson_data = Lesson.query.filter_by(lesson_id=lesson_id).all()

    if lesson_data:
        # กระบวนการแปลงเส้นทางของไฟล์รูปภาพและไฟล์เสียงก่อนส่งไปที่เทมเพลต
        transformed_lesson_data = [(lesson.id, lesson.title, lesson.image_filename,
                                    lesson.sound_filename_thai, lesson.sound_filename_hmong_daw,
                                    lesson.sound_filename_hmong_njua, lesson.sound_filename_lahu,
                                    lesson.sound_filename_lisu, lesson.sound_filename_arka, lesson.sound_filename_karen,
                                    lesson.lesson_id)
                                   for lesson in lesson_data]

        return render_template('lesson.html', lesson_data=transformed_lesson_data, lesson_id=lesson_id)
    else:
        return "Lesson not found"
# ฟังก์ชันสำหรับตรวจสอบการเข้าสู่ระบบของนักเรียน

@app.route('/lesson_complete')
def lesson_complete():
    return render_template('lesson_complete.html')

def check_student_login(username, password):
    conn = sqlite3.connect('instance/questions.db')
    cursor = conn.cursor()

    # ค้นหาชื่อผู้ใช้และรหัสผ่านในฐานข้อมูล
    query = f"SELECT * FROM user WHERE username = ? AND password = ?"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()

    conn.close()

    return user is not None


# Route for the student login page
@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if check_student_login(username, password):
            session['username'] = username
            return redirect(url_for('student_dashboard'))
        else:
            error_message = 'ชื่อผู้ใช้หรือรหัสผ่านผิด'
            return render_template('student-login.html', error_message=error_message)
    else:
        return render_template('student-login.html')


def check_teacher_login(username, password):
    conn = sqlite3.connect('instance/questions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM user WHERE username = ? AND password = ?", (username, password))
    user_data = cursor.fetchone()
    conn.close()

    if user_data and user_data[0] == 'ครู':
        return True
    else:
        return False


@app.route('/teacher-login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')


        if check_teacher_login(username, password):
            session['username'] = username
            return redirect(url_for('teacher_dashboard'))
        else:
            error_message = 'ชื่อผู้ใช้หรือรหัสผ่านผิด หรือคุณไม่มีสิทธิ์ในการเข้าถึง'
            return render_template('teacher-login.html', error_message=error_message)
    else:
        return render_template('teacher-login.html')


@app.route('/teacher_dashboard')
def teacher_dashboard():
    total_students = User.query.filter_by(role='นักเรียน').count()

    return render_template('teacher_dashboard.html', total_students=total_students)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    is_user_added = False
    is_username_taken = False
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        surname = request.form['surname']
        age = request.form['age']
        role = request.form['role']


        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            is_username_taken = True
        else:
            new_user = User(username=username, password=password, name=name, surname=surname, age=age, role=role)
            db.session.add(new_user)
            db.session.commit()
            is_user_added = True

    return render_template('add_user.html', is_user_added=is_user_added, is_username_taken=is_username_taken)


@app.route('/view_users')
def view_users():
    users = User.query.all()
    return render_template('view_users.html', users=users)

@app.route('/view_students')
def view_students():
    students = User.query.filter_by(role='นักเรียน').all()
    return render_template('view_students.html', students=students)

@app.route('/remove_student/<int:student_id>', methods=['POST'])
def remove_student(student_id):
    student = User.query.get(student_id)
    if student:
        db.session.delete(student)
        db.session.commit()
    return redirect(url_for('view_students'))

@app.route('/study_page')
def study_page():
    return render_template('study_page.html')

@app.route('/quiz')
def quiz():
    questions = Question.query.all()
    return render_template('quiz.html', questions=questions)



@app.route('/add_lesson', methods=['GET', 'POST'])
def add_lesson():
    if request.method == 'POST':
        lesson_id = request.form['lesson_id']
        lesson_title = request.form['lesson_title']

        if 'image_filename' in request.files:
            image = request.files['image_filename']
            if image.filename != '':
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = f"/uploads/{filename}"
            else:
                image_filename = None
        else:
            image_filename = None

        # Check if Thai sound file was uploaded
        if 'sound_filename_thai' in request.files:
            sound_thai = request.files['sound_filename_thai']
            if sound_thai.filename != '':
                filename = secure_filename(sound_thai.filename)
                sound_thai.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                sound_filename_thai = f"/uploads/{filename}"
            else:
                sound_filename_thai = None
        else:
            sound_filename_thai = None

        if 'sound_filename_hmong_daw' in request.files:
            sound_hmong_daw = request.files['sound_filename_hmong_daw']
            if sound_hmong_daw.filename != '':
                filename = secure_filename(sound_hmong_daw.filename)
                sound_hmong_daw.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                sound_filename_hmong_daw = f"/uploads/{filename}"
            else:
                sound_filename_hmong_daw = None
        else:
            sound_filename_hmong_daw = None

        if 'sound_filename_hmong_njua' in request.files:
            sound_hmong_njua = request.files['sound_filename_hmong_njua']
            if sound_hmong_njua.filename != '':
                filename = secure_filename(sound_hmong_njua.filename)
                sound_hmong_njua.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                sound_filename_hmong_njua = f"/uploads/{filename}"
            else:
                sound_filename_hmong_njua = None
        else:
            sound_filename_hmong_njua = None

        if 'sound_filename_lahu' in request.files:
            sound_lahu = request.files['sound_filename_lahu']
            if sound_lahu.filename != '':
                filename = secure_filename(sound_lahu.filename)
                sound_lahu.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                sound_filename_lahu = f"/uploads/{filename}"
            else:
                sound_filename_lahu = None
        else:
            sound_filename_lahu = None

        if 'sound_filename_lisu' in request.files:
            sound_lisu = request.files['sound_filename_lisu']
            if sound_lisu.filename != '':
                filename = secure_filename(sound_lisu.filename)
                sound_lisu.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                sound_filename_lisu = f"/uploads/{filename}"
            else:
                sound_filename_lisu = None
        else:
            sound_filename_lisu = None

        if 'sound_filename_arka' in request.files:
            sound_arka = request.files['sound_filename_arka']
            if sound_arka.filename != '':
                filename = secure_filename(sound_arka.filename)
                sound_arka.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                sound_filename_arka = f"/uploads/{filename}"
            else:
                sound_filename_arka = None
        else:
            sound_filename_arka = None
        if 'sound_filename_karen' in request.files:
            sound_karen = request.files['sound_filename_karen']
            if sound_karen.filename != '':
                filename = secure_filename(sound_karen.filename)
                sound_karen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                sound_filename_karen = f"/uploads/{filename}"
            else:
                sound_filename_karen = None
        else:
            sound_filename_karen = None

        new_lesson = Lesson(
            lesson_id=lesson_id,
            title=lesson_title,
            image_filename=image_filename,
            sound_filename_thai=sound_filename_thai,
            sound_filename_hmong_daw=sound_filename_hmong_daw,
            sound_filename_hmong_njua=sound_filename_hmong_njua,
            sound_filename_lahu=sound_filename_lahu,
            sound_filename_lisu=sound_filename_lisu,
            sound_filename_arka=sound_filename_arka,
            sound_filename_karen=sound_filename_karen,
        )

        db.session.add(new_lesson)
        db.session.commit()

        return redirect(url_for('lesson_select'))

    return render_template('add_lesson.html')

def get_all_lessons():
    connection = sqlite3.connect('instance/questions.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM lesson')
    lessons = cursor.fetchall()
    connection.close()
    return lessons

def get_all_submit():
    connection = sqlite3.connect('instance/questions.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM submit_report')
    lessons = cursor.fetchall()
    connection.close()
    return lessons


@app.route('/view_lessons')
def view_lessons():
    lessons = get_all_lessons()
    return render_template('view_lessons.html', lessons=lessons)

@app.route('/delete_lesson/<int:lesson_id>', methods=['POST'])
def delete_lesson(lesson_id):
    lesson = Lesson.query.get(lesson_id)
    if lesson:
        db.session.delete(lesson)
        db.session.commit()
        flash(f'บทเรียน "{lesson.title}" ถูกลบออกจากฐานข้อมูล', 'success')
    else:
        flash('ไม่พบบทเรียนที่ต้องการลบในฐานข้อมูล', 'danger')

    return redirect(url_for('view_lessons'))

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        question_text = request.form['question']
        lesson_id = int(request.form['lesson'])

        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = f"static/uploads/{filename}"
            else:
                image_path = None
        else:
            image_path = None

        new_question = Question(question=question_text, image=image_path, lesson=lesson_id)
        db.session.add(new_question)
        db.session.commit()

        return redirect('/view')

    return render_template('add_question.html')
@app.route('/view')
def view_questions():
    questions = Question.query.all()
    return render_template('view.html', questions=questions)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_question(id):
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    return redirect('/view')

if __name__ == '__main__':
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        os.chmod(upload_folder, 0o755)

    create_tables()

    app.run(debug=False)

