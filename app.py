import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import config
from agents.architecture_analyzer import ArchitectureAnalyzer
from agents.policy_checker import PolicyChecker
from agents.bicep_generator import BicepGenerator
from utils.file_processor import FileProcessor
from utils.zip_generator import ZipGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# Allowed file extensions
ALLOWED_EXTENSIONS = config.ALLOWED_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    environment = request.form.get('environment', 'development')
    
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the file through the AI agents
        try:
            result = process_architecture_diagram(filepath, environment)
            return jsonify({
                'success': True,
                'message': 'File processed successfully',
                'download_url': url_for('download_result', filename=result['zip_filename'])
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error processing file: {str(e)}'
            })
    
    return jsonify({
        'success': False,
        'message': 'Invalid file type. Please upload PNG, JPG, PDF, XML, Draw.io, VSDX, or SVG files.'
    })

def process_architecture_diagram(filepath, environment):
    """Process the architecture diagram through the 3 AI agents"""
    
    # Initialize the AI agents
    arch_analyzer = ArchitectureAnalyzer()
    policy_checker = PolicyChecker()
    bicep_generator = BicepGenerator()
    
    # Initialize file processor
    file_processor = FileProcessor()
    
    # Step 1: Extract content from the uploaded file
    extracted_content = file_processor.process_file(filepath)
    
    # Step 2: Analyze architecture with Agent 1
    architecture_analysis = arch_analyzer.analyze_architecture(extracted_content)
    
    # Step 3: Check policy compliance with Agent 2
    policy_compliance = policy_checker.check_compliance(architecture_analysis, environment)
    
    # Step 4: Generate bicep templates and YAML pipelines with Agent 3
    bicep_templates = bicep_generator.generate_bicep_templates(
        architecture_analysis, 
        policy_compliance
    )
    
    # Step 5: Create ZIP file with all generated content
    zip_generator = ZipGenerator()
    zip_filename = zip_generator.create_zip_package(
        bicep_templates,
        architecture_analysis,
        policy_compliance,
        environment
    )
    
    return {
        'zip_filename': zip_filename,
        'architecture_analysis': architecture_analysis,
        'policy_compliance': policy_compliance
    }

@app.route('/download/<filename>')
def download_result(filename):
    try:
        return send_file(
            os.path.join('output', filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('index'))

@app.route('/download-sample/<sample_type>')
def download_sample(sample_type):
    """Download sample architecture diagrams for testing"""
    try:
        sample_files = {
            'svg': ('sample-azure-architecture.svg', 'Sample Azure Architecture (SVG)'),
            'drawio': ('sample-azure-architecture.drawio', 'Sample Azure Architecture (Draw.io)'),
            'txt': ('sample-architecture-description.txt', 'Sample Architecture Description (Text)')
        }
        
        if sample_type not in sample_files:
            flash('Invalid sample type')
            return redirect(url_for('index'))
            
        filename, description = sample_files[sample_type]
        filepath = os.path.join('static', 'samples', filename)
        
        if not os.path.exists(filepath):
            flash(f'Sample file not found: {filename}')
            return redirect(url_for('index'))
            
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error downloading sample: {str(e)}')
        return redirect(url_for('index'))

@app.route('/samples')
def list_samples():
    """API endpoint to list available sample files"""
    samples = [
        {
            'type': 'svg',
            'name': 'Azure Web App Architecture (SVG)',
            'description': 'Visual diagram showing a 3-tier Azure web application with Front Door, App Service, SQL Database, and monitoring components',
            'download_url': url_for('download_sample', sample_type='svg')
        },
        {
            'type': 'drawio',
            'name': 'Azure Web App Architecture (Draw.io)',
            'description': 'Draw.io XML format of the same architecture - perfect for testing XML processing',
            'download_url': url_for('download_sample', sample_type='drawio')
        },
        {
            'type': 'txt',
            'name': 'Architecture Description (Text)',
            'description': 'Detailed text description of Azure architecture components and data flow',
            'download_url': url_for('download_sample', sample_type='txt')
        }
    ]
    return jsonify({'samples': samples})

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=config.DEBUG, host='0.0.0.0', port=5000)
