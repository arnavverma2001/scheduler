import openai
import json
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'  # You can customize this to your needs
Session(app)


openai.api_key = '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'

# API endpoint manually add employees
@app.route('/add_employee_api', methods=['POST'])
def add_employee_api():
    data = request.json
    employee_id = data['id']
    availability = data['availability']

    # Add employee to session
    session.setdefault('employees', [])
    session['employees'].append({'id': employee_id, 'availability': availability})

    return jsonify({'message': 'Employee added successfully'})

# API endpoint to list employees
@app.route('/list_employees_api', methods=['GET'])
def list_employees_api():
    return jsonify(session.get('employees', []))

# Display mainpage
@app.route('/')
def home():
    session.setdefault('employees', [])
    session.setdefault('constraints', [])
    session.setdefault('store_hours', {})
    return render_template('index.html', employees=session['employees'], constraints=session['constraints'], store_hours=session['store_hours'])

# UI endpoint to add employees, general constraints, and store hours
@app.route('/add_employee', methods=['POST'])
def add_employee():
    employee_id = request.form['id']
    availability = request.form['availability'].split(',')

    # Retrieve existing session data or initialize if not present
    session_employees = session.get('employees', [])
    session_constraints = session.get('constraints', [])
    session_store_hours = session.get('store_hours', {})

    # Add the new employee to the session data
    session_employees.append({'id': employee_id, 'availability': availability})

    # Update session data
    session['employees'] = session_employees
    session['constraints'] = session_constraints
    session['store_hours'] = session_store_hours

    return render_template('index.html', employees=session_employees, constraints=session_constraints, store_hours=session_store_hours)

# UI endpoint to add general schedule constraints
@app.route('/add_constraint', methods=['POST'])
def add_constraint():
    constraint = request.form['constraint']

    # Retrieve existing session data or initialize if not present
    session_employees = session.get('employees', [])
    session_constraints = session.get('constraints', [])
    session_store_hours = session.get('store_hours', {})

    # Add the new constraint to the session data
    session_constraints.append(constraint)

    # Update session data
    session['employees'] = session_employees
    session['constraints'] = session_constraints
    session['store_hours'] = session_store_hours

    return render_template('index.html', employees=session_employees, constraints=session_constraints, store_hours=session_store_hours)


# UI endpoint to generate and display the schedule using ChatGPT
@app.route('/generate_schedule', methods=['GET'])
def generate_schedule():
    session.setdefault('employees', [])
    session.setdefault('constraints', [])
    session.setdefault('store_hours', [])
    
    # Prepare data for ChatGPT
    data_for_gpt = {
        'employees': session['employees'],
        'constraints': session['constraints'],
        'store_hours': session['store_hours']
    }

    # Convert data to text or structured format (customize based on your needs)
    input_text = f"Generate a schedule with the following information, make sure all store hours before close and after open are accounted for and highlight hours when no-one is scheduled and the store is open. Output the full response called schedule in a codified dictionary (do not add any other words) format with day, employee, and hour {data_for_gpt}"

    # Make API request to ChatGPT
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": input_text}
        ],
        max_tokens=500,
        temperature=0
    )
    print("DATA GOING TO API:", data_for_gpt)
    print("RESPONSE FROM API:",response)
    # Extract and display the generated schedule
    generated_schedule = json.loads(response['choices'][0]['message']['content'])

    print("SCHEDULE DICT:", generated_schedule)

    # Render the main page with the generated schedule
    return render_template('index.html', employees=session['employees'], constraints=session['constraints'],
                           store_hours=session['store_hours'], generated_schedule=generated_schedule)

# UI endpoint to add store hours
@app.route('/add_store_hours', methods=['POST'])
def add_store_hours():
    day = request.form['day']
    open_time = request.form['open_time']
    close_time = request.form['close_time']

    # Retrieve existing session data or initialize if not present
    session_employees = session.get('employees', [])
    session_constraints = session.get('constraints', [])
    session_store_hours = session.get('store_hours', {})

    # Add the new store hours to the session data
    session_store_hours[day] = {'open_time': open_time, 'close_time': close_time}

    # Update session data
    session['employees'] = session_employees
    session['constraints'] = session_constraints
    session['store_hours'] = session_store_hours

    return render_template('index.html', employees=session_employees, constraints=session_constraints, store_hours=session_store_hours)

@app.before_request
def clear_entries():
    if 'reset_session' in request.args:
        session.clear()
    else:
        session.setdefault('employees', [])
        session.setdefault('constraints', [])
        session.setdefault('store_hours', {})

if __name__ == '__main__':
    app.run(debug=True)
