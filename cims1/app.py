from flask import Flask, request, render_template, redirect, url_for
import os
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/analyse')
def analyse():
    return render_template('analyse.html')


@app.route('/view_table')
def view_table_landing():
    # This serves as the default "View Table" page
    return render_template('view_table_landing.html') 

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        return redirect(url_for('select_type', filepath=filepath))
    else:
        return "File type not allowed", 400

@app.route('/select_type')
def select_type():
    filepath = request.args.get('filepath')
    return render_template('select_type.html', filepath=filepath)
 # Introduced new template

@app.route('/view_table/<course_type>')
def view_table(course_type):
    filepath = request.args.get('filepath')
    if not filepath or not os.path.exists(filepath):
        return "File not found or invalid filepath", 400

    data = pd.read_csv(filepath)
    data.columns = data.columns.str.strip()  # Clean column names

    # Ensure required columns exist
    required_columns = {'TYPE', 'YEAR', 'ADMITTED', 'VACANT', 'COURSE'}
    if not required_columns.issubset(data.columns):
        return "ERROR: Missing one or more required columns in the CSV file", 400

    # Filter data by course type
    filtered_data = data[data['TYPE'] == course_type.upper()]
    return render_template('view_table.html', course_type=course_type.upper(), filtered_data=filtered_data)


@app.route('/view_graphs/<course_type>')
def view_graphs(course_type):
    filepath = request.args.get('filepath')
    data = pd.read_csv(filepath)

    # Clean the column names
    data.columns = data.columns.str.strip()

    # Check if necessary columns exist
    required_columns = {'TYPE', 'YEAR', 'ADMITTED', 'VACANT', 'COURSE'}
    if not required_columns.issubset(data.columns):
        return "ERROR: Missing one or more required columns in the CSV file", 400

    # Filter the data based on the selected course type
    filtered_data = data[data['TYPE'] == course_type.upper()]

    # Generate graphs
    admitted_fig = generate_graph(filtered_data, "YEAR", "ADMITTED", f"Admitted Students in {course_type.upper()} Courses")
    vacant_fig = generate_graph(filtered_data, "YEAR", "VACANT", f"Vacant Seats in {course_type.upper()} Courses")
    course_fig = generate_graph(filtered_data, "COURSE", "ADMITTED", f"Admissions per Course in {course_type.upper()}")

    # Convert graphs to base64 strings
    admitted_img = fig_to_base64(admitted_fig)
    vacant_img = fig_to_base64(vacant_fig)
    course_img = fig_to_base64(course_fig)

    return render_template(
        'display.html',
        course_type=course_type.upper(),
        admitted_img=admitted_img,
        vacant_img=vacant_img,
        course_img=course_img
    )



def generate_graph(data, x_col, y_col, title):
    from matplotlib import pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    import io
    import base64

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(data[x_col], data[y_col], color='pink', width=0.4)
    ax.set_xlabel(x_col.capitalize())
    ax.set_ylabel(y_col.capitalize())
    ax.set_title(title)
    return fig

def fig_to_base64(fig):
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    import io
    import base64

    buf = io.BytesIO()
    FigureCanvas(fig).print_png(buf)
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_str

if __name__ == '__main__':
    app.run(debug=True)
