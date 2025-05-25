from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class PeriodRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

@app.route('/')
def home():
    todos = Todo.query.all()
    notes = Note.query.all()
    period_records = PeriodRecord.query.all()
    return render_template('index.html', todos=todos, notes=notes, period_records=period_records)

@app.route('/add_todo', methods=['POST'])
def add_todo():
    text = request.form.get('text')
    if text:
        new_todo = Todo(text=text)
        db.session.add(new_todo)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/toggle_todo/<int:todo_id>', methods=['POST'])
def toggle_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.completed = not todo.completed
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete_todo/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/add_note', methods=['POST'])
def add_note():
    text = request.form.get('text')
    if text:
        new_note = Note(text=text)
        db.session.add(new_note)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete_note/<int:note_id>')
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/add_period', methods=['POST'])
def add_period():
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
    new_record = PeriodRecord(start_date=start_date, end_date=end_date)
    db.session.add(new_record)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete_period/<int:record_id>')
def delete_period(record_id):
    record = PeriodRecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)