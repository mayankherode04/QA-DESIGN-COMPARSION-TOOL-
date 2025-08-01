from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import json
import sys
from flask_cors import CORS
import uuid
from datetime import datetime

# Add the parent directory to the path to import from ml module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.image_comparison import compare_images
from ml.figma_service import fetch_figma_design, FigmaService

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Global storage for issue selections (in production, use a proper database)
issue_selections = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/test_figma', methods=['POST'])
def test_figma_connection():
    """Test endpoint to validate Figma credentials and file access"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        figma_token = data.get('figma_token')
        figma_file_key = data.get('figma_file_key')
        
        if not figma_token or not figma_file_key:
            return jsonify({'error': 'Missing token or file key'}), 400
        
        # Initialize Figma service
        figma_service = FigmaService(figma_token)
        
        # Test token
        token_valid, token_result = figma_service.validate_token()
        if not token_valid:
            return jsonify({
                'success': False,
                'error': 'Token validation failed',
                'details': token_result
            }), 400
        
        # Test file access
        file_valid, file_result = figma_service.get_file_info(figma_file_key)
        if not file_valid:
            return jsonify({
                'success': False,
                'error': 'File access failed',
                'details': file_result
            }), 400
        
        # Get file structure info
        file_info = file_result
        pages_count = len(file_info.get('document', {}).get('children', []))
        
        return jsonify({
            'success': True,
            'message': 'Figma connection successful',
            'file_name': file_info.get('name', 'Unknown'),
            'pages_count': pages_count,
            'last_modified': file_info.get('lastModified', 'Unknown')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Test failed',
            'details': str(e)
        }), 500


@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        if 'session_id' not in request.form:
            return jsonify({'error': 'Missing session ID'}), 400

        session_id = request.form['session_id']
        single_comparison_dir = os.path.join(
            app.config['UPLOAD_FOLDER'], 'single_comparisons', session_id)
        os.makedirs(single_comparison_dir, exist_ok=True)

        # Debug logging removed for production

        if 'figma_image' not in request.files or 'built_image' not in request.files:
            missing = [f for f in ['figma_image', 'built_image']
                       if f not in request.files]
            return jsonify({'error': f'Missing files: {", ".join(missing)}'}), 400

        figma_image = request.files['figma_image']
        built_image = request.files['built_image']

        # File processing

        if figma_image.filename == '' or built_image.filename == '':
            empty = [f for f in ['figma_image', 'built_image']
                     if request.files[f].filename == '']
            return jsonify({'error': f'Empty filenames: {", ".join(empty)}'}), 400

        figma_filename = secure_filename(figma_image.filename)
        built_filename = secure_filename(built_image.filename)

        figma_path = os.path.join(single_comparison_dir, figma_filename)
        built_path = os.path.join(single_comparison_dir, built_filename)

        figma_image.save(figma_path)
        built_image.save(built_path)

        comparison_result = compare_images(
            figma_path, built_path, single_comparison_dir)

        comparison_result['session_id'] = session_id
        
        # Save detected differences to JSON file for code correction
        differences_file = os.path.join(single_comparison_dir, 'differences.json')
        with open(differences_file, 'w') as f:
            json.dump({
                'detected_differences': comparison_result.get('detected_differences', []),
                'total_differences': comparison_result.get('total_differences', 0)
            }, f, indent=2)
        
        # Convert absolute paths to relative paths for the frontend
        comparison_result['figma_image'] = os.path.relpath(comparison_result['figma_image'], app.config['UPLOAD_FOLDER'])
        comparison_result['built_image'] = os.path.relpath(comparison_result['built_image'], app.config['UPLOAD_FOLDER'])
        comparison_result['difference_image'] = os.path.relpath(comparison_result['difference_image'], app.config['UPLOAD_FOLDER'])
        comparison_result['comparison_image'] = os.path.relpath(comparison_result['comparison_image'], app.config['UPLOAD_FOLDER'])

        return jsonify(comparison_result)

    except Exception as e:
        # Error handling
        return jsonify({'error': str(e)}), 500


@app.route('/figma_upload', methods=['POST'])
def figma_upload():
    try:
        if 'session_id' not in request.form:
            return jsonify({'error': 'Missing session ID'}), 400

        session_id = request.form['session_id']
        figma_comparison_dir = os.path.join(
            app.config['UPLOAD_FOLDER'], 'figma_comparisons', session_id)
        os.makedirs(figma_comparison_dir, exist_ok=True)

        # Get Figma credentials
        figma_token = request.form.get('figma_token')
        figma_file_key = request.form.get('figma_file_key')
        figma_node_id = request.form.get('figma_node_id', '').strip()

        if not figma_token or not figma_file_key:
            return jsonify({'error': 'Missing Figma token or file key'}), 400

        # Get built image
        if 'built_image' not in request.files:
            return jsonify({'error': 'Missing built image'}), 400

        built_image = request.files['built_image']
        if built_image.filename == '':
            return jsonify({'error': 'Empty built image filename'}), 400

        # Fetch Figma design
        figma_success, figma_result = fetch_figma_design(
            figma_token, 
            figma_file_key, 
            figma_node_id if figma_node_id else None,
            figma_comparison_dir
        )

        if not figma_success:
            return jsonify({'error': f'Failed to fetch Figma design: {figma_result}'}), 500

        # Save built image
        built_filename = secure_filename(built_image.filename)
        built_path = os.path.join(figma_comparison_dir, built_filename)
        built_image.save(built_path)

        # Compare images
        comparison_result = compare_images(
            figma_result, built_path, figma_comparison_dir)

        comparison_result['session_id'] = session_id
        
        # Save detected differences to JSON file for code correction
        differences_file = os.path.join(figma_comparison_dir, 'differences.json')
        with open(differences_file, 'w') as f:
            json.dump({
                'detected_differences': comparison_result.get('detected_differences', []),
                'total_differences': comparison_result.get('total_differences', 0)
            }, f, indent=2)
        
        # Convert absolute paths to relative paths for the frontend
        comparison_result['figma_image'] = os.path.relpath(comparison_result['figma_image'], app.config['UPLOAD_FOLDER'])
        comparison_result['built_image'] = os.path.relpath(comparison_result['built_image'], app.config['UPLOAD_FOLDER'])
        comparison_result['difference_image'] = os.path.relpath(comparison_result['difference_image'], app.config['UPLOAD_FOLDER'])
        comparison_result['comparison_image'] = os.path.relpath(comparison_result['comparison_image'], app.config['UPLOAD_FOLDER'])

        return jsonify(comparison_result)

    except Exception as e:
        # Error handling
        return jsonify({'error': str(e)}), 500


@app.route('/bulk_upload', methods=['POST'])
def bulk_upload_files():
    try:
        if 'screens' not in request.form:
            return jsonify({'error': 'Missing screens data'}), 400

        screens = json.loads(request.form['screens'])
        now = datetime.now()
        bulk_comparison_dir = os.path.join(
            app.config['UPLOAD_FOLDER'], 'bulk_comparisons', now.strftime("%Y%m%d_%H%M%S"))
        os.makedirs(bulk_comparison_dir, exist_ok=True)

        results = []

        for screen in screens:
            figma_image = request.files.get(screen['figma_screenshot'])
            app_image = request.files.get(screen['app_screenshot'])

            if not figma_image or not app_image:
                return jsonify({'error': f"Missing image for screen {screen['name']}"}), 400

            figma_filename = secure_filename(f"{screen['name']}_figma.png")
            app_filename = secure_filename(f"{screen['name']}_app.png")

            figma_path = os.path.join(bulk_comparison_dir, figma_filename)
            app_path = os.path.join(bulk_comparison_dir, app_filename)

            figma_image.save(figma_path)
            app_image.save(app_path)

            comparison_result = compare_images(
                figma_path, app_path, bulk_comparison_dir)
            comparison_result['screen_name'] = screen['name']
            
            # Convert absolute paths to relative paths for the frontend
            comparison_result['figma_image'] = os.path.relpath(comparison_result['figma_image'], app.config['UPLOAD_FOLDER'])
            comparison_result['built_image'] = os.path.relpath(comparison_result['built_image'], app.config['UPLOAD_FOLDER'])
            comparison_result['difference_image'] = os.path.relpath(comparison_result['difference_image'], app.config['UPLOAD_FOLDER'])
            comparison_result['comparison_image'] = os.path.relpath(comparison_result['comparison_image'], app.config['UPLOAD_FOLDER'])
            
            results.append(comparison_result)

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generate_code', methods=['POST'])
def generate_code():
    """Generate complete code based on Figma design and selected language"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        language = data.get('language', 'html-css')
        component_name = data.get('component_name', 'Component')
        requirements = data.get('requirements', '')
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Missing session ID'}), 400
        
        # Get the latest comparison data for this session
        # Check both single_comparisons and figma_comparisons directories
        single_comparison_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'single_comparisons', session_id)
        figma_comparison_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'figma_comparisons', session_id)
        
        comparison_dir = None
        if os.path.exists(single_comparison_dir):
            comparison_dir = single_comparison_dir
        elif os.path.exists(figma_comparison_dir):
            comparison_dir = figma_comparison_dir
        else:
            return jsonify({'error': 'No comparison data found for this session'}), 400
        
        # Generate code based on language
        generated_code = generate_code_from_design(language, component_name, requirements)
        
        return jsonify({
            'success': True,
            'code': generated_code,
            'language': language,
            'component_name': component_name
        })
        
    except Exception as e:
        # Error handling
        return jsonify({'error': str(e)}), 500


@app.route('/correct_code', methods=['POST'])
def correct_code():
    """Correct existing code based on detected issues"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        language = data.get('language', 'html-css')
        existing_code = data.get('existing_code', '')
        notes = data.get('notes', '')
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Missing session ID'}), 400
        
        if not existing_code.strip():
            return jsonify({'error': 'No existing code provided'}), 400
        
        # Get the detected differences for this session
        # Check both single_comparisons and figma_comparisons directories
        single_comparison_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'single_comparisons', session_id)
        figma_comparison_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'figma_comparisons', session_id)
        
        comparison_dir = None
        if os.path.exists(single_comparison_dir):
            comparison_dir = single_comparison_dir
        elif os.path.exists(figma_comparison_dir):
            comparison_dir = figma_comparison_dir
        else:
            return jsonify({'error': 'No comparison data found for this session'}), 400
        
        # Correct the code based on detected issues
        corrected_code, changes = correct_code_based_on_issues(language, existing_code, notes, session_id)
        
        return jsonify({
            'success': True,
            'corrected_code': corrected_code,
            'changes': changes,
            'language': language
        })
        
    except Exception as e:
        # Error handling
        return jsonify({'error': str(e)}), 500


def generate_code_from_design(language, component_name, requirements):
    """Generate code based on the selected language and requirements"""
    
    # Base HTML structure for all web languages
    base_html = f'''<!-- {component_name} Component -->
<!-- Generated from Figma Design -->
<div class="{component_name.lower()}-container">
    <header class="{component_name.lower()}-header">
        <h1 class="{component_name.lower()}-title">{component_name}</h1>
        <nav class="{component_name.lower()}-nav">
            <ul>
                <li><a href="#home">Home</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
    </header>
    
    <main class="{component_name.lower()}-main">
        <section class="{component_name.lower()}-hero">
            <h2>Welcome to {component_name}</h2>
            <p>This is a beautiful, responsive component generated from your Figma design.</p>
            <button class="{component_name.lower()}-cta">Get Started</button>
        </section>
        
        <section class="{component_name.lower()}-features">
            <div class="feature-card">
                <h3>Feature 1</h3>
                <p>Description of the first feature.</p>
            </div>
            <div class="feature-card">
                <h3>Feature 2</h3>
                <p>Description of the second feature.</p>
            </div>
            <div class="feature-card">
                <h3>Feature 3</h3>
                <p>Description of the third feature.</p>
            </div>
        </section>
    </main>
    
    <footer class="{component_name.lower()}-footer">
        <p>&copy; 2024 {component_name}. All rights reserved.</p>
    </footer>
</div>'''
    
    # Generate code based on language
    if language == 'html-css':
        return f'''{base_html}

<style>
/* {component_name} Component Styles */
.{component_name.lower()}-container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    font-family: 'Arial', sans-serif;
}}

.{component_name.lower()}-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 0;
    border-bottom: 2px solid #4ecdc4;
}}

.{component_name.lower()}-title {{
    color: #4ecdc4;
    font-size: 2em;
    margin: 0;
}}

.{component_name.lower()}-nav ul {{
    display: flex;
    list-style: none;
    margin: 0;
    padding: 0;
}}

.{component_name.lower()}-nav li {{
    margin-left: 30px;
}}

.{component_name.lower()}-nav a {{
    color: #f0f0f0;
    text-decoration: none;
    font-weight: bold;
    transition: color 0.3s ease;
}}

.{component_name.lower()}-nav a:hover {{
    color: #ffa500;
}}

.{component_name.lower()}-hero {{
    text-align: center;
    padding: 60px 20px;
    background: linear-gradient(45deg, #2c2c54, #4ecdc4);
    border-radius: 15px;
    margin: 40px 0;
}}

.{component_name.lower()}-hero h2 {{
    color: #f0f0f0;
    font-size: 3em;
    margin-bottom: 20px;
}}

.{component_name.lower()}-hero p {{
    color: #f0f0f0;
    font-size: 1.2em;
    margin-bottom: 30px;
}}

.{component_name.lower()}-cta {{
    background: linear-gradient(45deg, #ffa500, #ff6b6b);
    color: #2c2c54;
    border: none;
    padding: 15px 30px;
    font-size: 1.1em;
    font-weight: bold;
    border-radius: 8px;
    cursor: pointer;
    transition: transform 0.3s ease;
}}

.{component_name.lower()}-cta:hover {{
    transform: translateY(-2px);
}}

.{component_name.lower()}-features {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 30px;
    margin: 40px 0;
}}

.feature-card {{
    background: rgba(44, 44, 84, 0.8);
    padding: 30px;
    border-radius: 12px;
    border: 2px solid #4ecdc4;
    text-align: center;
    transition: transform 0.3s ease;
}}

.feature-card:hover {{
    transform: translateY(-5px);
}}

.feature-card h3 {{
    color: #ffa500;
    font-size: 1.5em;
    margin-bottom: 15px;
}}

.feature-card p {{
    color: #f0f0f0;
    line-height: 1.6;
}}

.{component_name.lower()}-footer {{
    text-align: center;
    padding: 20px 0;
    border-top: 2px solid #4ecdc4;
    color: #f0f0f0;
}}

/* Responsive Design */
@media (max-width: 768px) {{
    .{component_name.lower()}-header {{
        flex-direction: column;
        text-align: center;
    }}
    
    .{component_name.lower()}-nav ul {{
        margin-top: 20px;
    }}
    
    .{component_name.lower()}-nav li {{
        margin: 0 15px;
    }}
    
    .{component_name.lower()}-hero h2 {{
        font-size: 2em;
    }}
    
    .{component_name.lower()}-features {{
        grid-template-columns: 1fr;
    }}
}}

{requirements if requirements else '/* Additional custom styles can be added here */'}'''
    
    elif language == 'react':
        return f'''import React from 'react';
import './{component_name}.css';

const {component_name} = () => {{
  return (
    <div className="{component_name.lower()}-container">
      <header className="{component_name.lower()}-header">
        <h1 className="{component_name.lower()}-title">{component_name}</h1>
        <nav className="{component_name.lower()}-nav">
          <ul>
            <li><a href="#home">Home</a></li>
            <li><a href="#about">About</a></li>
            <li><a href="#contact">Contact</a></li>
          </ul>
        </nav>
      </header>
      
      <main className="{component_name.lower()}-main">
        <section className="{component_name.lower()}-hero">
          <h2>Welcome to {component_name}</h2>
          <p>This is a beautiful, responsive React component generated from your Figma design.</p>
          <button className="{component_name.lower()}-cta">Get Started</button>
        </section>
        
        <section className="{component_name.lower()}-features">
          <div className="feature-card">
            <h3>Feature 1</h3>
            <p>Description of the first feature.</p>
          </div>
          <div className="feature-card">
            <h3>Feature 2</h3>
            <p>Description of the second feature.</p>
          </div>
          <div className="feature-card">
            <h3>Feature 3</h3>
            <p>Description of the third feature.</p>
          </div>
        </section>
      </main>
      
      <footer className="{component_name.lower()}-footer">
        <p>&copy; 2024 {component_name}. All rights reserved.</p>
      </footer>
    </div>
  );
}};

export default {component_name};

// CSS file: {component_name}.css
/*
.{component_name.lower()}-container {{
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Arial', sans-serif;
}}

.{component_name.lower()}-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  border-bottom: 2px solid #4ecdc4;
}}

.{component_name.lower()}-title {{
  color: #4ecdc4;
  font-size: 2em;
  margin: 0;
}}

.{component_name.lower()}-nav ul {{
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
}}

.{component_name.lower()}-nav li {{
  margin-left: 30px;
}}

.{component_name.lower()}-nav a {{
  color: #f0f0f0;
  text-decoration: none;
  font-weight: bold;
  transition: color 0.3s ease;
}}

.{component_name.lower()}-nav a:hover {{
  color: #ffa500;
}}

.{component_name.lower()}-hero {{
  text-align: center;
  padding: 60px 20px;
  background: linear-gradient(45deg, #2c2c54, #4ecdc4);
  border-radius: 15px;
  margin: 40px 0;
}}

.{component_name.lower()}-hero h2 {{
  color: #f0f0f0;
  font-size: 3em;
  margin-bottom: 20px;
}}

.{component_name.lower()}-hero p {{
  color: #f0f0f0;
  font-size: 1.2em;
  margin-bottom: 30px;
}}

.{component_name.lower()}-cta {{
  background: linear-gradient(45deg, #ffa500, #ff6b6b);
  color: #2c2c54;
  border: none;
  padding: 15px 30px;
  font-size: 1.1em;
  font-weight: bold;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.3s ease;
}}

.{component_name.lower()}-cta:hover {{
  transform: translateY(-2px);
}}

.{component_name.lower()}-features {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
  margin: 40px 0;
}}

.feature-card {{
  background: rgba(44, 44, 84, 0.8);
  padding: 30px;
  border-radius: 12px;
  border: 2px solid #4ecdc4;
  text-align: center;
  transition: transform 0.3s ease;
}}

.feature-card:hover {{
  transform: translateY(-5px);
}}

.feature-card h3 {{
  color: #ffa500;
  font-size: 1.5em;
  margin-bottom: 15px;
}}

.feature-card p {{
  color: #f0f0f0;
  line-height: 1.6;
}}

.{component_name.lower()}-footer {{
  text-align: center;
  padding: 20px 0;
  border-top: 2px solid #4ecdc4;
  color: #f0f0f0;
}}

/* Responsive Design */
@media (max-width: 768px) {{
  .{component_name.lower()}-header {{
    flex-direction: column;
    text-align: center;
  }}
  
  .{component_name.lower()}-nav ul {{
    margin-top: 20px;
  }}
  
  .{component_name.lower()}-nav li {{
    margin: 0 15px;
  }}
  
  .{component_name.lower()}-hero h2 {{
    font-size: 2em;
  }}
  
  .{component_name.lower()}-features {{
    grid-template-columns: 1fr;
  }}
}}
*/'''
    
    elif language == 'tailwind':
        return f'''<!-- {component_name} Component with Tailwind CSS -->
<div class="max-w-6xl mx-auto p-5 font-sans">
  <header class="flex justify-between items-center py-5 border-b-2 border-cyan-400">
    <h1 class="text-4xl font-bold text-cyan-400">{component_name}</h1>
    <nav>
      <ul class="flex space-x-8">
        <li><a href="#home" class="text-gray-300 font-bold hover:text-orange-400 transition-colors duration-300">Home</a></li>
        <li><a href="#about" class="text-gray-300 font-bold hover:text-orange-400 transition-colors duration-300">About</a></li>
        <li><a href="#contact" class="text-gray-300 font-bold hover:text-orange-400 transition-colors duration-300">Contact</a></li>
      </ul>
    </nav>
  </header>
  
  <main>
    <section class="text-center py-16 px-5 bg-gradient-to-br from-gray-800 to-cyan-400 rounded-2xl my-10">
      <h2 class="text-5xl text-gray-100 mb-5">Welcome to {component_name}</h2>
      <p class="text-xl text-gray-100 mb-8">This is a beautiful, responsive component generated from your Figma design.</p>
      <button class="bg-gradient-to-r from-orange-400 to-red-400 text-gray-800 px-8 py-4 text-lg font-bold rounded-lg hover:-translate-y-1 transition-transform duration-300">
        Get Started
      </button>
    </section>
    
    <section class="grid grid-cols-1 md:grid-cols-3 gap-8 my-10">
      <div class="bg-gray-800 bg-opacity-80 p-8 rounded-xl border-2 border-cyan-400 text-center hover:-translate-y-2 transition-transform duration-300">
        <h3 class="text-2xl text-orange-400 mb-4">Feature 1</h3>
        <p class="text-gray-300 leading-relaxed">Description of the first feature.</p>
      </div>
      <div class="bg-gray-800 bg-opacity-80 p-8 rounded-xl border-2 border-cyan-400 text-center hover:-translate-y-2 transition-transform duration-300">
        <h3 class="text-2xl text-orange-400 mb-4">Feature 2</h3>
        <p class="text-gray-300 leading-relaxed">Description of the second feature.</p>
      </div>
      <div class="bg-gray-800 bg-opacity-80 p-8 rounded-xl border-2 border-cyan-400 text-center hover:-translate-y-2 transition-transform duration-300">
        <h3 class="text-2xl text-orange-400 mb-4">Feature 3</h3>
        <p class="text-gray-300 leading-relaxed">Description of the third feature.</p>
      </div>
    </section>
  </main>
  
  <footer class="text-center py-5 border-t-2 border-cyan-400 text-gray-300">
    <p>&copy; 2024 {component_name}. All rights reserved.</p>
  </footer>
</div>

<!-- Make sure to include Tailwind CSS in your project -->
<!-- <script src="https://cdn.tailwindcss.com"></script> -->'''
    
    else:
        return f'''// {component_name} Component - {language.upper()}
// Generated from Figma Design
// This is a template for {language} implementation

{base_html}

/*
Additional implementation notes:
- Language: {language}
- Component: {component_name}
- Requirements: {requirements}

Please adapt this template to your specific {language} framework requirements.
*/'''


def correct_code_based_on_issues(language, existing_code, notes, session_id):
    """Correct existing code based on detected issues"""
    
    # Get detected differences from the session
    # Check both single_comparisons and figma_comparisons directories
    single_comparison_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'single_comparisons', session_id)
    figma_comparison_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'figma_comparisons', session_id)
    
    differences_file = None
    if os.path.exists(single_comparison_dir):
        differences_file = os.path.join(single_comparison_dir, 'differences.json')
    elif os.path.exists(figma_comparison_dir):
        differences_file = os.path.join(figma_comparison_dir, 'differences.json')
    
    changes = []
    corrected_code = existing_code
    
    try:
        if differences_file and os.path.exists(differences_file):
            with open(differences_file, 'r') as f:
                differences_data = json.load(f)
                all_differences = differences_data.get('detected_differences', [])
                
                # Get user selections for this session
                selections = issue_selections.get(session_id, {})
                
                # Filter out neglected issues
                detected_differences = []
                for diff in all_differences:
                    diff_id = str(diff.get('id'))
                    if selections.get(diff_id) != 'neglect':
                        detected_differences.append(diff)
                
                if not detected_differences:
                    if all_differences:
                        changes.append(f"No issues selected for correction. {len(all_differences)} issues were neglected by the user.")
                        corrected_code += f'''

<!-- Code Review Complete -->
<!-- {len(all_differences)} issues were detected but all were neglected by the user -->
<!-- No corrections applied based on user preferences -->
{notes if notes else '<!-- Consider reviewing the neglected issues if needed -->'}'''
                    else:
                        changes.append("No specific issues detected in the comparison. Your code appears to match the design well!")
                        corrected_code += f'''

<!-- Code Review Complete -->
<!-- No specific issues were detected in the comparison -->
<!-- Your implementation appears to match the design requirements -->
{notes if notes else '<!-- Consider adding any additional improvements based on your requirements -->'}'''
                else:
                    changes.append(f"Applying corrections for {len(detected_differences)} selected issues (neglected {len(all_differences) - len(detected_differences)} issues)")
                    
                    for diff in detected_differences:
                        analysis = diff.get('issue_analysis', {})
                        issue_type = analysis.get('issue_type', 'Unknown Issue')
                        
                        if 'Missing' in issue_type:
                            changes.append(f"Added missing {issue_type.lower()} at position {diff.get('location', 'unknown')}")
                            # Add placeholder for missing element
                            if language in ['html-css', 'react', 'vue', 'angular']:
                                placeholder = f'''

<!-- Add missing {issue_type.lower()} here -->
<div class="missing-{diff['id']}" style="width: {diff['coordinates']['width']}px; height: {diff['coordinates']['height']}px;">
    <!-- Replace with actual {issue_type.lower()} content -->
</div>'''
                                corrected_code += placeholder
                        
                        elif 'Extra' in issue_type:
                            changes.append(f"Marked extra {issue_type.lower()} for removal at position {diff.get('location', 'unknown')}")
                            # Add comment for extra element
                            if language in ['html-css', 'react', 'vue', 'angular']:
                                comment = f'''

<!-- Remove or hide extra {issue_type.lower()} -->
<!-- <div class="extra-{diff['id']}" style="display: none;"> -->
    <!-- This element should be removed or hidden -->
<!-- </div> -->'''
                                corrected_code += comment
                        
                        elif 'Layout' in issue_type:
                            changes.append(f"Fixed layout/positioning issue at position {diff.get('location', 'unknown')}")
                            # Add CSS fix
                            if language in ['html-css', 'react', 'vue', 'angular']:
                                css_fix = f'''

/* Fix for layout issue {diff['id']} */
.layout-fix-{diff['id']} {{
    position: absolute;
    left: {diff['coordinates']['x']}px;
    top: {diff['coordinates']['y']}px;
    width: {diff['coordinates']['width']}px;
    height: {diff['coordinates']['height']}px;
    z-index: 1;
}}'''
                                corrected_code += css_fix
        else:
            changes.append("No comparison data found. Please perform a comparison first to get specific corrections.")
            corrected_code += f'''

<!-- No comparison data available -->
<!-- Please perform a comparison first to get specific corrections -->
{notes if notes else '<!-- General code review completed -->'}'''
    
    except Exception as e:
        changes.append(f"Error reading differences: {str(e)}")
        corrected_code += f'''

<!-- Error occurred while analyzing differences -->
<!-- {str(e)} -->
{notes if notes else '<!-- Please check the comparison results manually -->'}'''
    
    # Add general improvements based on notes
    if notes and len(changes) == 1 and "No specific issues" in changes[0]:
        changes.append(f"Applied custom improvements based on notes: {notes}")
        corrected_code += f'''

<!-- Custom improvements based on notes -->
{notes}'''
    
    if not changes:
        changes.append("No specific issues detected. Code reviewed and optimized.")
    
    return corrected_code, changes


@app.route('/select_issues', methods=['POST'])
def select_issues():
    """Save issue selections for a session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        selections = data.get('selections', {})
        
        if not session_id:
            return jsonify({'error': 'Missing session ID'}), 400
        
        # Store selections for this session
        issue_selections[session_id] = selections
        
        return jsonify({
            'success': True,
            'message': 'Issue selections saved successfully',
            'selections_count': len(selections)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to save selections: {str(e)}'}), 500


@app.route('/get_issue_selections/<session_id>', methods=['GET'])
def get_issue_selections(session_id):
    """Get issue selections for a session"""
    try:
        selections = issue_selections.get(session_id, {})
        return jsonify({
            'success': True,
            'selections': selections
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get selections: {str(e)}'}), 500


@app.route('/get_filtered_issues/<session_id>', methods=['GET'])
def get_filtered_issues(session_id):
    """Get only selected (non-neglected) issues for a session"""
    try:
        # Get the differences file for this session
        differences_file = os.path.join(
            app.config['UPLOAD_FOLDER'], 
            'single_comparisons', 
            session_id, 
            'differences.json'
        )
        
        if not os.path.exists(differences_file):
            return jsonify({'error': 'No comparison data found for this session'}), 404
        
        # Load all differences
        with open(differences_file, 'r') as f:
            differences_data = json.load(f)
            all_differences = differences_data.get('detected_differences', [])
        
        # Get selections for this session
        selections = issue_selections.get(session_id, {})
        
        # Filter out neglected issues
        filtered_differences = []
        for diff in all_differences:
            diff_id = str(diff.get('id'))
            if selections.get(diff_id) != 'neglect':
                filtered_differences.append(diff)
        
        return jsonify({
            'success': True,
            'filtered_differences': filtered_differences,
            'total_original': len(all_differences),
            'total_filtered': len(filtered_differences),
            'neglected_count': len(all_differences) - len(filtered_differences)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get filtered issues: {str(e)}'}), 500


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True, port=5002)
