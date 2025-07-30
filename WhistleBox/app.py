from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime
import pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///complaints_v4.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    complaint = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    incident_time = db.Column(db.DateTime, nullable=False)
    incident_place = db.Column(db.String(100), nullable=False)
    issue_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Pending')

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/hosteller')
def hosteller():
    return redirect(url_for('index'))

@app.route('/index')
def index():
    complaints = Complaint.query.order_by(Complaint.timestamp.desc()).all()
    return render_template('index.html', complaints=complaints)

@app.route('/submit', methods=['POST'])
def submit():
    title = request.form.get('title')
    complaint_text = request.form.get('complaint')
    location = request.form.get('location')
    category = request.form.get('category')

    # For simplicity, we'll use the current time as the incident time
    incident_time = datetime.datetime.utcnow()

    new_complaint = Complaint(
        title=title,
        complaint=complaint_text,
        incident_time=incident_time,
        incident_place=location,
        issue_type=category
    )
    db.session.add(new_complaint)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/submission-success')
def submission_success():
    return "Your complaint has been registered."

def format_datetime(value, format='medium'):
    if format == 'full':
        format="EEEE, d. MMMM y 'at' HH:mm:ss"
    elif format == 'medium':
        format="EE dd.MM.y HH:mm"
    try:
        utc_dt = pytz.utc.localize(value)
        local_tz = pytz.timezone('Asia/Kolkata')
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return value

app.jinja_env.filters['datetime'] = format_datetime


@app.route('/admin')
def admin():
    complaints = Complaint.query.order_by(Complaint.timestamp.desc()).all()
    total = Complaint.query.count()
    pending = Complaint.query.filter_by(status='Pending').count()
    resolved = Complaint.query.filter_by(status='Resolved').count()
    rejected = Complaint.query.filter_by(status='Rejected').count()
    summary = {'total': total, 'pending': pending, 'resolved': resolved, 'rejected': rejected}
    return render_template('admin.html', complaints=complaints, summary=summary)


@app.route('/admin/search', methods=['POST'])
def admin_search():
    search_term = request.form.get('search')
    location = request.form.get('location')
    month = request.form.get('month')
    status = request.form.get('status')

    query = Complaint.query

    if search_term:
        query = query.filter(
            (Complaint.title.contains(search_term)) |
            (Complaint.complaint.contains(search_term)) |
            (Complaint.incident_place.contains(search_term)) |
            (Complaint.issue_type.contains(search_term))
        )
    
    if location:
        query = query.filter(Complaint.incident_place == location)

    if month:
        from sqlalchemy import extract
        query = query.filter(extract('month', Complaint.timestamp) == month)

    if status:
        query = query.filter(Complaint.status == status)

    complaints = query.order_by(Complaint.timestamp.desc()).all()
    
    total = Complaint.query.count()
    pending = Complaint.query.filter_by(status='Pending').count()
    resolved = Complaint.query.filter_by(status='Resolved').count()
    rejected = Complaint.query.filter_by(status='Rejected').count()
    summary = {'total': total, 'pending': pending, 'resolved': resolved, 'rejected': rejected}
    return render_template('admin.html', complaints=complaints, summary=summary)


@app.route('/update_status/<int:complaint_id>', methods=['POST'])
def update_status(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    complaint.status = request.form.get('status')
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/delete_complaint/<int:complaint_id>', methods=['POST'])
def delete_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    db.session.delete(complaint)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/complaint/<int:complaint_id>')
def get_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    return jsonify({
        'id': complaint.id,
        'title': complaint.title,
        'complaint': complaint.complaint,
        'status': complaint.status,
        'incident_place': complaint.incident_place,
        'category': complaint.issue_type
    })

@app.route('/statistics')
def statistics():
    total = Complaint.query.count()
    pending = Complaint.query.filter_by(status='Pending').count()
    resolved = Complaint.query.filter_by(status='Resolved').count()
    rejected = Complaint.query.filter_by(status='Rejected').count()
    summary = {'total': total, 'pending': pending, 'resolved': resolved, 'rejected': rejected}
    return render_template('statistics.html', summary=summary)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
