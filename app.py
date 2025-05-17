from flask import Flask, request, render_template_string
import os
import csv
from shipping_lookup import lookup_sku

app = Flask(__name__)

# Directories and files
script_dir = os.path.dirname(os.path.abspath(__file__))
feedback_file = os.path.join(script_dir, 'feedback.csv')
upload_folder = os.path.join(script_dir, 'uploads')
os.makedirs(upload_folder, exist_ok=True)

# HTML template with lookup, feedback, and upload forms
TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Shipping Cost Lookup</title>
  <style>
    body { font-family: sans-serif; padding: 2rem; max-width: 600px; margin: auto; }
    form { margin-top: 1.5rem; }
    label { display: block; margin-bottom: 0.3rem; }
    input[type="text"], input[type="number"], input[type="file"] { width: 100%; padding: 0.5rem; margin-bottom: 0.5rem; }
    button { padding: 0.5rem 1rem; }
    #output, .message { margin-top: 1rem; font-weight: bold; }
  </style>
</head>
<body>
  <h1>Shipping Cost Lookup</h1>
  <form method="post" action="/">
    <label for="sku">Lookup SKU:</label>
    <input type="text" id="sku" name="sku" placeholder="Enter SKU" required>
    <button type="submit">Go</button>
  </form>
  {% if lookup_result %}
    <div id="output">{{ lookup_result }}</div>
  {% endif %}

  <h2>Submit Actual Shipping Cost</h2>
  <form method="post" action="/feedback">
    <label for="fb-sku">SKU:</label>
    <input type="text" id="fb-sku" name="sku" placeholder="Enter SKU" required>
    <label for="fb-cost">Shipping Cost ($):</label>
    <input type="number" step="0.01" id="fb-cost" name="cost" placeholder="e.g. 15.99" required>
    <button type="submit">Submit</button>
  </form>
  {% if feedback_msg %}
    <div class="message">{{ feedback_msg }}</div>
  {% endif %}

  <h2>Upload CSV of Shipments</h2>
  <form method="post" action="/upload" enctype="multipart/form-data">
    <label for="file">CSV File:</label>
    <input type="file" id="file" name="file" accept=".csv" required>
    <button type="submit">Upload</button>
  </form>
  {% if upload_msg %}
    <div class="message">{{ upload_msg }}</div>
  {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    lookup_result = None
    if request.method == 'POST':
        sku = request.form.get('sku', '').strip()
        if sku:
            lookup_result = lookup_sku(sku)
    return render_template_string(
        TEMPLATE,
        lookup_result=lookup_result,
        feedback_msg=None,
        upload_msg=None
    )

@app.route('/feedback', methods=['POST'])
def feedback():
    sku = request.form.get('sku', '').strip().upper()
    cost = request.form.get('cost', '').strip()
    msg = ''
    if sku and cost:
        try:
            cost_val = float(cost)
            write_header = not os.path.exists(feedback_file)
            with open(feedback_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow(['SKU', 'shipping_cost'])
                writer.writerow([sku, cost_val])
            msg = f"Recorded shipping cost ${cost_val:.2f} for SKU {sku}."
        except ValueError:
            msg = "Invalid cost value."
    else:
        msg = "SKU and cost are required."
    return render_template_string(
        TEMPLATE,
        lookup_result=None,
        feedback_msg=msg,
        upload_msg=None
    )

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    msg = ''
    if file and file.filename.lower().endswith('.csv'):
        filepath = os.path.join(upload_folder, file.filename)
        file.save(filepath)
        write_header = not os.path.exists(feedback_file)
        try:
            with open(filepath, newline='') as f_in, open(feedback_file, 'a', newline='') as f_fb:
                reader = csv.DictReader(f_in)
                writer = csv.writer(f_fb)
                if write_header:
                    writer.writerow(['SKU', 'shipping_cost'])
                for row in reader:
                    sku = row.get('SKU', '').strip().upper()
                    cost_val = row.get('delivery_cost') or row.get('shipping_cost') or ''
                    try:
                        c = float(cost_val)
                        writer.writerow([sku, c])
                    except:
                        pass
            msg = f"Uploaded and recorded {file.filename}."
        except Exception as e:
            msg = f"Error processing file: {e}"
    else:
        msg = "Please upload a .csv file."
    return render_template_string(
        TEMPLATE,
        lookup_result=None,
        feedback_msg=None,
        upload_msg=msg
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)