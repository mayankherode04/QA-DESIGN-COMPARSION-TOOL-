# Design Comparison Tool

A powerful web-based tool that compares Figma design screenshots with implemented UI screenshots using advanced computer vision techniques. Built with Flask, OpenCV, and modern web technologies, it helps developers and designers identify visual discrepancies between design mockups and actual implementations.

## 🚀 Key Features

- **Smart Image Comparison**: Uses Structural Similarity Index (SSIM) and contour detection to identify visual differences
- **Issue Selection System**: Selectively choose which detected issues to keep or neglect before code generation
- **Code Generation**: Automatically generates corrected code based on detected issues
- **Figma Integration**: Direct integration with Figma API for seamless design import
- **Bulk Processing**: Compare multiple design-implementation pairs simultaneously
- **Modern UI**: Futuristic sci-fi design with responsive, mobile-friendly interface

## 🛠️ Technical Stack

- **Backend**: Flask, Python, OpenCV, scikit-image
- **Frontend**: HTML5, CSS3, JavaScript, Modern CSS Animations
- **Image Processing**: Advanced computer vision algorithms
- **API Integration**: Figma API for design file access

## 📁 Project Structure

```
design-compare-tool/
├── frontend/          # Modern web interface
│   ├── templates/     # HTML templates
│   └── static/        # CSS, JS, and assets
├── backend/           # Flask API and business logic
│   ├── app.py         # Main Flask application
│   └── requirements.txt
├── ml/                # Computer vision algorithms
│   ├── image_comparison.py
│   └── figma_service.py
└── uploads/           # Temporary file storage
```

## 🔧 How to Run

### Option 1: Using main.py (Recommended)
```bash
python main.py
```

### Option 2: Using the backend directly
```bash
cd backend
python app.py
```

The application will be available at `http://localhost:5000`

## 🎯 How It Works

1. **Upload Images**: Upload Figma design screenshots and implemented UI screenshots
2. **Advanced Analysis**: Algorithms analyze structural similarities and detect visual differences
3. **Issue Selection**: Interactive interface allows you to choose which problems to address
4. **Code Generation**: Generate corrected code that only fixes your selected issues
5. **Real-time Results**: Get comparison results with visual annotations

## 🖼️ Image Comparison Technical Details

The image comparison process uses several computer vision techniques:

1. **Image Preprocessing**:
   - Both images are read using OpenCV
   - Figma design image is resized to match built screen dimensions
   - Images are converted to grayscale for analysis

2. **Structural Similarity Index (SSIM)**:
   - Uses scikit-image's structural_similarity function
   - Measures similarity based on luminance, contrast, and structure
   - Returns similarity score and difference image

3. **Difference Analysis**:
   - Binary threshold applied using Otsu's method
   - Contour detection to identify significant differences
   - Visual highlighting of differences on both images

4. **Visualization**:
   - Green rectangles on Figma design (missing elements)
   - Red rectangles on built screen (extra elements)
   - Filled difference image for clear comparison

## 🎨 Issue Selection Feature

The tool includes a powerful issue selection system:

- **Keep/Neglect Buttons**: Each detected issue has "Keep" and "Neglect" options
- **Visual Feedback**: Selected issues highlighted in green, neglected in red
- **Bulk Controls**: "Select All" or "Neglect All" for efficiency
- **Smart Filtering**: Code generation only applies fixes for selected issues
- **Session Persistence**: Selections saved per comparison session

## 🎨 UI Design Features

The interface features a futuristic sci-fi design with:

- **Animated Background**: Dynamic particle effects and gradient animations
- **Neon Glow Effects**: Multiple color layers with cyan, orange, and purple themes
- **Interactive Animations**: Smooth hover effects and transitions
- **Glass-morphism**: Backdrop blur effects and transparency
- **Responsive Design**: Mobile-optimized with touch-friendly interactions

## 📱 Mobile Support

The interface is fully responsive and optimized for mobile devices:
- Stacked layout for selection controls
- Larger touch targets for buttons
- Optimized spacing and typography
- Touch-friendly interactions

## 🔌 API Endpoints

- `GET /`: Main application page
- `POST /upload`: Single image comparison
- `POST /figma_upload`: Figma integration upload
- `POST /bulk_upload`: Multiple image comparison
- `POST /generate_code`: Generate code from design
- `POST /correct_code`: Correct existing code
- `POST /select_issues`: Save issue selections
- `GET /uploads/<filename>`: Serve uploaded files

## 📦 Dependencies

Install required dependencies:
```bash
cd backend
pip install -r requirements.txt
```

Or install individually:
```bash
pip install flask flask-cors opencv-python pillow numpy werkzeug
```

## 🎯 Use Cases

- **QA Testing**: Verify UI implementations match design specifications
- **Design Reviews**: Identify visual inconsistencies in web applications
- **Development Workflow**: Streamline the design-to-code process
- **Regression Testing**: Ensure UI changes don't break existing designs

## 🚀 Benefits

1. **Precision**: Only fix issues that matter to you
2. **Efficiency**: Skip irrelevant or false-positive issues
3. **Control**: Full control over what gets corrected
4. **Flexibility**: Easy to change selections before generating code
5. **Persistence**: Selections are saved per session

Perfect for development teams, QA engineers, and designers who need to ensure pixel-perfect implementations of their designs.

## 🚀 Getting Started

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)
- Git (for cloning the repository)

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd design-compare-tool
   ```

2. **Navigate to the project directory**
   ```bash
   cd design-compare-tool
   ```

3. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   # Option 1: Using main.py (Recommended)
   python main.py
   
   # Option 2: Using backend directly
   cd backend
   python app.py
   ```

5. **Access the application**
   - Open your web browser
   - Go to: `http://localhost:5000` (if using main.py)
   - Go to: `http://localhost:5002` (if using backend directly)

### 🛠️ Troubleshooting

#### Common Issues and Solutions

**Issue 1: ModuleNotFoundError for Flask**
```bash
# Solution: Install Flask and dependencies
pip install flask flask-cors opencv-python pillow numpy werkzeug
```

**Issue 2: Port already in use**
```bash
# Solution 1: Kill the process using the port
# On Windows:
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F

# Solution 2: Use a different port
python main.py --port 5001
```

**Issue 3: Permission denied error**
```bash
# Solution: Run with administrator privileges
# On Windows: Right-click PowerShell and "Run as Administrator"
# On Mac/Linux:
sudo python main.py
```

**Issue 4: OpenCV installation error**
```bash
# Solution: Install OpenCV separately
pip uninstall opencv-python
pip install opencv-python-headless
```

**Issue 5: scikit-image installation error**
```bash
# Solution: Install alternative image processing libraries
pip install pillow numpy
# Note: The tool will work without scikit-image, but with reduced functionality
```

**Issue 6: File not found error**
```bash
# Solution: Ensure you're in the correct directory
pwd  # Check current directory
ls   # List files to verify you're in the right place
cd design-compare-tool  # Navigate to project root if needed
```

**Issue 7: Virtual environment issues**
```bash
# Solution: Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 🔧 Development Setup

For developers who want to contribute:

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/design-compare-tool.git
   cd design-compare-tool
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # OR
   source venv/bin/activate  # Mac/Linux
   ```

3. **Install development dependencies**
   ```bash
   pip install -r backend/requirements.txt
   pip install pytest  # For testing
   ```

4. **Run in development mode**
   ```bash
   python main.py
   ```

### 📱 Testing the Application

1. **Upload test images**
   - Upload your own Figma design and implementation screenshots
   - Or use any design comparison images you have

2. **Compare designs**
   - Click "Compare" to analyze the images
   - Review detected differences

3. **Select issues**
   - Use the issue selection interface
   - Choose which problems to address

4. **Generate code**
   - Use the code generation feature
   - Get corrected code based on selected issues

### 🚨 Emergency Commands

If the application crashes or becomes unresponsive:

```bash
# Kill all Python processes
taskkill /f /im python.exe  # Windows
pkill -f python             # Mac/Linux

# Clear temporary files
rm -rf uploads/*            # Mac/Linux
Remove-Item -Recurse -Force uploads\*  # Windows

# Restart the application
python main.py
```

## 📸 Features Showcase

The application features a stunning futuristic UI with:
- Animated particle effects and gradient backgrounds
- Neon glow effects with multiple color layers
- Interactive hover animations and smooth transitions
- Glass-morphism design elements
- Fully responsive mobile-optimized interface

Built with modern web technologies and advanced computer vision algorithms for precise design comparison and code generation.
