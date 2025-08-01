document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("upload-form");
  const figmaForm = document.getElementById("figma-form");
  const resultDiv = document.getElementById("result");
  const comparisonImagesDiv = document.getElementById("comparison-images");
  const figmaDropArea = document.getElementById("figma-drop-area");
  const builtDropArea = document.getElementById("built-drop-area");
  const figmaApiDropArea = document.getElementById("figma-api-drop-area");
  const figmaInput = document.getElementById("figma-image");
  const builtInput = document.getElementById("built-image");
  const figmaApiInput = document.getElementById("figma-api-image");
  const compareBtn = document.getElementById("compare-btn");
  const figmaCompareBtn = document.getElementById("figma-compare-btn");
  const testConnectionBtn = document.getElementById("test-connection-btn");
  const testResultDiv = document.getElementById("test-result");
  const modeBtns = document.querySelectorAll(".mode-btn");

  // Generate a unique session ID
  const sessionId = generateSessionId();
  // Store session ID globally for code generation functions
  window.currentSessionId = sessionId;

  // Mode switching functionality
  modeBtns.forEach(btn => {
    btn.addEventListener("click", function() {
      const mode = this.getAttribute("data-mode");
      
      // Update active button
      modeBtns.forEach(b => b.classList.remove("active"));
      this.classList.add("active");
      
      // Show/hide forms
      if (mode === "screenshot") {
        form.classList.add("active");
        figmaForm.classList.remove("active");
      } else {
        form.classList.remove("active");
        figmaForm.classList.add("active");
      }
      
      // Clear results
      resultDiv.innerHTML = "";
      comparisonImagesDiv.style.display = "none";
      document.getElementById("detected-differences").style.display = "none";
      clearSelectedDifferences();
      testResultDiv.innerHTML = "";
      testResultDiv.className = "test-result";
    });
  });

  function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.add("dragover");
  }

  function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove("dragover");
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove("dragover");

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      const input = this.querySelector('input[type="file"]');
      input.files = files;
      displayImage(this, file);
      checkInputs();
    }
  }

  function handleClick() {
    this.querySelector('input[type="file"]').click();
  }

  function displayImage(dropArea, file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      const img = document.createElement("img");
      img.src = e.target.result;
      img.classList.add("preview-image");
      dropArea.innerHTML = "";
      dropArea.appendChild(img);
    };
    reader.readAsDataURL(file);
  }

  function checkInputs() {
    // Check screenshot mode inputs
    if (figmaInput.files.length > 0 && builtInput.files.length > 0) {
      compareBtn.disabled = false;
    } else {
      compareBtn.disabled = true;
    }
    
    // Check Figma API mode inputs
    const figmaToken = document.getElementById("figma-token").value.trim();
    const figmaFileKey = document.getElementById("figma-file-key").value.trim();
    if (figmaToken && figmaFileKey && figmaApiInput.files.length > 0) {
      figmaCompareBtn.disabled = false;
    } else {
      figmaCompareBtn.disabled = true;
    }
  }

  // Add event listeners for all drop areas
  [figmaDropArea, builtDropArea, figmaApiDropArea].forEach((dropArea) => {
    dropArea.addEventListener("dragover", handleDragOver);
    dropArea.addEventListener("dragleave", handleDragLeave);
    dropArea.addEventListener("drop", handleDrop);
    dropArea.addEventListener("click", handleClick);
  });

  // Add event listeners for all file inputs
  [figmaInput, builtInput, figmaApiInput].forEach((input) => {
    input.addEventListener("change", function (e) {
      if (this.files.length > 0) {
        displayImage(this.parentElement, this.files[0]);
        checkInputs();
      }
    });
  });

  // Add event listeners for Figma credential inputs
  document.getElementById("figma-token").addEventListener("input", checkInputs);
  document.getElementById("figma-file-key").addEventListener("input", checkInputs);
  document.getElementById("figma-node-id").addEventListener("input", checkInputs);

  // Test connection button
  testConnectionBtn.addEventListener("click", function() {
    const figmaToken = document.getElementById("figma-token").value.trim();
    const figmaFileKey = document.getElementById("figma-file-key").value.trim();
    
    if (!figmaToken || !figmaFileKey) {
      showTestResult("Please enter both token and file key", "error");
      return;
    }
    
    // Show loading state
    testConnectionBtn.disabled = true;
    testConnectionBtn.textContent = "Testing...";
    testResultDiv.innerHTML = "";
    testResultDiv.className = "test-result";
    
    // Test the connection
    fetch("/test_figma", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        figma_token: figmaToken,
        figma_file_key: figmaFileKey
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showTestResult(
          `✅ Connection successful!<br>
           File: ${data.file_name}<br>
           Pages: ${data.pages_count}<br>
           Last Modified: ${new Date(data.last_modified).toLocaleString()}`, 
          "success"
        );
      } else {
        showTestResult(`❌ ${data.error}: ${data.details}`, "error");
      }
    })
    .catch(error => {
      showTestResult(`❌ Test failed: ${error.message}`, "error");
    })
    .finally(() => {
      testConnectionBtn.disabled = false;
      testConnectionBtn.textContent = "Test Connection";
    });
  });

  function showTestResult(message, type) {
    testResultDiv.innerHTML = message;
    testResultDiv.className = `test-result ${type}`;
  }

  // Screenshot vs Screenshot form submission
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    handleScreenshotComparison();
  });

  // Figma API vs Screenshot form submission
  figmaForm.addEventListener("submit", function (e) {
    e.preventDefault();
    handleFigmaComparison();
  });

  function handleScreenshotComparison() {
    // Show loading state
    compareBtn.disabled = true;
    compareBtn.textContent = "Processing...";
    resultDiv.innerHTML = '<p>Processing images...</p>';
    comparisonImagesDiv.style.display = 'none';
    document.getElementById("detected-differences").style.display = 'none';
    const codeGenerationSection = document.getElementById("code-generation");
    if (codeGenerationSection) codeGenerationSection.style.display = 'none';
    clearSelectedDifferences();

    var formData = new FormData();

    // Add session ID to form data
    formData.append("session_id", sessionId);

    // Ensure files are added to FormData
    if (figmaInput.files.length > 0) {
      formData.append("figma_image", figmaInput.files[0]);
    }
    if (builtInput.files.length > 0) {
      formData.append("built_image", builtInput.files[0]);
    }

    // Log the form data
    for (var pair of formData.entries()) {
      console.log(pair[0] + ": " + pair[1]);
    }

    fetch("/upload", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        console.log("Response status:", response.status);
        console.log("Response headers:", response.headers);
        return response.json();
      })
      .then((data) => {
        if (data.error) {
          throw new Error(data.error);
        }
        
        // Display similarity results
        resultDiv.innerHTML = `
          <h2>Comparison Result</h2>
          <p class="similarity">Similarity: ${data.similarity}%</p>
          <p>${data.message}</p>
        `;
        
        // Display comparison images
        displayComparisonImages(data);
        
        // Reset button
        compareBtn.disabled = false;
        compareBtn.textContent = "Compare Screenshots";
      })
      .catch((error) => {
        console.error("Error:", error);
        resultDiv.innerHTML = `<p>An error occurred: ${error.message}</p>`;
        compareBtn.disabled = false;
        compareBtn.textContent = "Compare Screenshots";
      });
  }

  function handleFigmaComparison() {
    // Show loading state
    figmaCompareBtn.disabled = true;
    figmaCompareBtn.textContent = "Fetching from Figma...";
    resultDiv.innerHTML = '<p>Fetching design from Figma...</p>';
    comparisonImagesDiv.style.display = 'none';
    document.getElementById("detected-differences").style.display = 'none';
    const codeGenerationSection = document.getElementById("code-generation");
    if (codeGenerationSection) codeGenerationSection.style.display = 'none';
    clearSelectedDifferences();

    var formData = new FormData();

    // Add session ID to form data
    formData.append("session_id", sessionId);

    // Add Figma credentials
    formData.append("figma_token", document.getElementById("figma-token").value);
    formData.append("figma_file_key", document.getElementById("figma-file-key").value);
    
    const nodeId = document.getElementById("figma-node-id").value.trim();
    if (nodeId) {
      formData.append("figma_node_id", nodeId);
    }

    // Add built image
    if (figmaApiInput.files.length > 0) {
      formData.append("built_image", figmaApiInput.files[0]);
    }

    // Log the form data (without sensitive token)
    for (var pair of formData.entries()) {
      if (pair[0] !== "figma_token") {
        console.log(pair[0] + ": " + pair[1]);
      } else {
        console.log(pair[0] + ": [HIDDEN]");
      }
    }

    fetch("/figma_upload", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        console.log("Response status:", response.status);
        console.log("Response headers:", response.headers);
        return response.json();
      })
      .then((data) => {
        if (data.error) {
          throw new Error(data.error);
        }
        
        // Display similarity results
        resultDiv.innerHTML = `
          <h2>Comparison Result</h2>
          <p class="similarity">Similarity: ${data.similarity}%</p>
          <p>${data.message}</p>
        `;
        
        // Display comparison images
        displayComparisonImages(data);
        
        // Reset button
        figmaCompareBtn.disabled = false;
        figmaCompareBtn.textContent = "Compare with Figma";
      })
      .catch((error) => {
        console.error("Error:", error);
        resultDiv.innerHTML = `<p>An error occurred: ${error.message}</p>`;
        figmaCompareBtn.disabled = false;
        figmaCompareBtn.textContent = "Compare with Figma";
      });
  }

  function displayComparisonImages(data) {
    const comparisonSection = document.getElementById("comparison-images");
    const figmaDisplay = document.getElementById("figma-display");
    const builtDisplay = document.getElementById("built-display");
    const differenceDisplay = document.getElementById("difference-display");
    
    // Debug: Log the image paths
    console.log('Image data received:', data);
    console.log('Figma image path:', data.figma_image);
    console.log('Built image path:', data.built_image);
    console.log('Difference image path:', data.difference_image);
    
    // Set image sources with proper URL construction
    const figmaUrl = `/uploads/${data.figma_image}`;
    const builtUrl = `/uploads/${data.built_image}`;
    const differenceUrl = `/uploads/${data.difference_image}`;
    
    console.log('Constructed URLs:');
    console.log('Figma URL:', figmaUrl);
    console.log('Built URL:', builtUrl);
    console.log('Difference URL:', differenceUrl);
    
    figmaDisplay.src = figmaUrl;
    builtDisplay.src = builtUrl;
    differenceDisplay.src = differenceUrl;
    
    // Add error handling for image loading
    figmaDisplay.onerror = function() {
      console.error('Failed to load figma image:', figmaUrl);
    };
    builtDisplay.onerror = function() {
      console.error('Failed to load built image:', builtUrl);
    };
    differenceDisplay.onerror = function() {
      console.error('Failed to load difference image:', differenceUrl);
    };
    
    // Show the comparison section
    comparisonSection.style.display = 'block';
    
    // Display detected differences if available
    if (data.detected_differences && data.detected_differences.length > 0) {
      displayDetectedDifferences(data.detected_differences, data.total_differences);
    }
    
    // Show code generation section
    const codeGenerationSection = document.getElementById("code-generation");
    if (codeGenerationSection) {
      codeGenerationSection.style.display = 'block';
    }
    
    // Scroll to the comparison section
    comparisonSection.scrollIntoView({ behavior: 'smooth' });
  }

  function displayDetectedDifferences(differences, totalDifferences) {
    const differencesSection = document.getElementById("detected-differences");
    const totalDifferencesSpan = document.getElementById("total-differences");
    const differencesGrid = document.getElementById("differences-grid");
    
    // Update total count
    totalDifferencesSpan.textContent = totalDifferences;
    
    // Initialize issue selections
    initializeIssueSelections(differences);
    
    // Clear existing differences
    differencesGrid.innerHTML = '';
    
    // Add issue selection controls
    const selectionControls = document.createElement('div');
    selectionControls.className = 'issue-selection-controls';
    selectionControls.innerHTML = `
      <div class="selection-summary">
        <span class="selection-count">Selected: <span id="selected-count">0</span></span>
        <span class="neglected-count">Neglected: <span id="neglected-count">0</span></span>
      </div>
      <div class="selection-buttons">
        <button class="select-all-btn" onclick="selectAllIssues()">Select All</button>
        <button class="neglect-all-btn" onclick="neglectAllIssues()">Neglect All</button>
        <button class="save-selections-btn" onclick="saveIssueSelections()">💾 Save Selections</button>
      </div>
    `;
    differencesGrid.appendChild(selectionControls);
    
    // Create difference cards
    differences.forEach(difference => {
      const differenceCard = document.createElement('div');
      differenceCard.className = 'difference-card';
      differenceCard.setAttribute('data-difference', JSON.stringify(difference));
      differenceCard.setAttribute('data-issue-id', difference.id);
      differenceCard.style.cursor = 'pointer';
      
      // Get issue analysis data
      const analysis = difference.issue_analysis || {};
      
      // Get current selection state
      const currentSelection = issueSelections[difference.id] || 'keep';
      const selectionClass = currentSelection === 'neglect' ? 'neglected' : 'selected';
      
      differenceCard.innerHTML = `
        <div class="difference-id">${difference.id}</div>
        <div class="issue-selection-buttons">
          <button class="keep-btn ${currentSelection === 'keep' ? 'active' : ''}" onclick="selectIssue(${difference.id}, 'keep')">
            ✅ Keep
          </button>
          <button class="neglect-btn ${currentSelection === 'neglect' ? 'active' : ''}" onclick="selectIssue(${difference.id}, 'neglect')">
            ❌ Neglect
          </button>
        </div>
        <div class="issue-category ${(analysis.issue_category || 'Content Issues').toLowerCase().replace(' ', '-')}">
          ${analysis.issue_category || 'Content Issues'}
        </div>
        <div class="difference-type">${analysis.issue_type || difference.type}</div>
        <div class="difference-description">${difference.description}</div>
        <div class="difference-details">
          <div class="detail-item">
            <div class="detail-label">Location</div>
            <div class="detail-value">${difference.location}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">Size</div>
            <div class="detail-value">${difference.size}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">Area</div>
            <div class="detail-value">${difference.area} px²</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">Severity</div>
            <div class="detail-value">
              <span class="difference-severity severity-${(analysis.severity || difference.severity).toLowerCase()}">${analysis.severity || difference.severity}</span>
            </div>
          </div>
        </div>
        
        <!-- Issue Analysis Section -->
        <div class="issue-analysis">
          <button class="analysis-toggle" onclick="toggleAnalysis(${difference.id})">
            📋 View Detailed Analysis & Fix Code
          </button>
          <div class="analysis-content" id="analysis-${difference.id}">
            <div class="issue-explanation">
              <strong>Issue Explanation:</strong><br>
              ${analysis.explanation || 'Detailed analysis not available for this issue.'}
            </div>
            
            <div class="code-snippet">
              <div class="code-snippet-header">
                <span class="code-snippet-title">Fix Code Snippet</span>
                <button class="copy-code-btn" onclick="copyCodeSnippet(${difference.id})">Copy Code</button>
              </div>
              <div class="code-content" id="code-${difference.id}">${analysis.code_snippet || '// No code snippet available for this issue'}</div>
            </div>
            
            <div class="fix-steps">
              <div class="fix-steps-title">Steps to Fix:</div>
              <ul class="fix-steps-list">
                ${(analysis.fix_steps || ['No specific steps available']).map(step => `<li>${step}</li>`).join('')}
              </ul>
            </div>
          </div>
        </div>
      `;
      
      // Add click event listener for highlighting (not for the analysis toggle)
      differenceCard.addEventListener('click', function(e) {
        // Don't trigger highlight if clicking on analysis toggle or content
        if (!e.target.closest('.analysis-toggle') && !e.target.closest('.analysis-content')) {
          toggleDifferenceHighlight(difference, this);
        }
      });
      
      differencesGrid.appendChild(differenceCard);
    });
    
    // Show the differences section
    differencesSection.style.display = 'block';
    
    // Scroll to the differences section
    differencesSection.scrollIntoView({ behavior: 'smooth' });
  }

  // Track selected differences
  let selectedDifferences = new Set();
  
  // Track issue selections (keep/neglect)
  let issueSelections = {};

  function toggleDifferenceHighlight(difference, cardElement) {
    const isSelected = selectedDifferences.has(difference.id);
    
    if (isSelected) {
      // Remove from selection
      selectedDifferences.delete(difference.id);
      cardElement.style.borderColor = '#4ecdc4';
      cardElement.style.boxShadow = '0 0 15px rgba(78, 205, 196, 0.3)';
    } else {
      // Add to selection
      selectedDifferences.add(difference.id);
      cardElement.style.borderColor = '#ff0000';
      cardElement.style.boxShadow = '0 0 20px rgba(255, 0, 0, 0.5)';
    }
    
    // Update highlights on all comparison images
    updateComparisonHighlights();
  }

  function updateComparisonHighlights() {
    const figmaHighlightBoxes = document.getElementById("figma-highlight-boxes");
    const builtHighlightBoxes = document.getElementById("built-highlight-boxes");
    const differenceHighlightBoxes = document.getElementById("difference-highlight-boxes");
    
    // Clear existing highlights
    figmaHighlightBoxes.innerHTML = '';
    builtHighlightBoxes.innerHTML = '';
    differenceHighlightBoxes.innerHTML = '';
    
    if (selectedDifferences.size === 0) {
      return;
    }
    
    // Get all differences data
    const allDifferences = [];
    document.querySelectorAll('.difference-card').forEach(card => {
      const differenceData = JSON.parse(card.getAttribute('data-difference'));
      if (selectedDifferences.has(differenceData.id)) {
        allDifferences.push(differenceData);
      }
    });
    
    // Create highlight boxes for each selected difference
    allDifferences.forEach((difference, index) => {
      const highlightBox = createHighlightBox(difference, index + 1);
      
      // Add to all three images
      figmaHighlightBoxes.appendChild(highlightBox.cloneNode(true));
      builtHighlightBoxes.appendChild(highlightBox.cloneNode(true));
      differenceHighlightBoxes.appendChild(highlightBox.cloneNode(true));
    });
    
    // Position the highlight boxes after images load
    setTimeout(() => {
      positionHighlightBoxes();
    }, 100);
  }

  function createHighlightBox(difference, number) {
    const highlightBox = document.createElement('div');
    highlightBox.className = 'highlight-box';
    highlightBox.textContent = number;
    highlightBox.setAttribute('data-difference-id', difference.id);
    return highlightBox;
  }

  function positionHighlightBoxes() {
    const images = ['figma-display', 'built-display', 'difference-display'];
    
    images.forEach(imageId => {
      const image = document.getElementById(imageId);
      const highlightBoxes = document.querySelectorAll(`#${imageId.replace('-display', '-highlight-boxes')} .highlight-box`);
      
      if (!image.complete) {
        image.onload = () => positionHighlightBoxes();
        return;
      }
      
      const imageRect = image.getBoundingClientRect();
      const imageWidth = image.naturalWidth;
      const imageHeight = image.naturalHeight;
      
      // Calculate the scale factor between displayed and natural image size
      const scaleX = imageRect.width / imageWidth;
      const scaleY = imageRect.height / imageHeight;
      
      highlightBoxes.forEach(box => {
        const differenceId = parseInt(box.getAttribute('data-difference-id'));
        const difference = getDifferenceById(differenceId);
        
        if (difference && difference.coordinates) {
          const x = difference.coordinates.x * scaleX;
          const y = difference.coordinates.y * scaleY;
          const width = difference.coordinates.width * scaleX;
          const height = difference.coordinates.height * scaleY;
          
          box.style.left = x + 'px';
          box.style.top = y + 'px';
          box.style.width = width + 'px';
          box.style.height = height + 'px';
        }
      });
    });
  }

  function getDifferenceById(id) {
    const card = document.querySelector(`[data-difference*='"id":${id}']`);
    if (card) {
      return JSON.parse(card.getAttribute('data-difference'));
    }
    return null;
  }

  // Global functions for analysis toggle and code copying
  window.toggleAnalysis = function(differenceId) {
    const analysisContent = document.getElementById(`analysis-${differenceId}`);
    const toggleBtn = analysisContent.previousElementSibling;
    
    if (analysisContent.classList.contains('active')) {
      analysisContent.classList.remove('active');
      toggleBtn.textContent = '📋 View Detailed Analysis & Fix Code';
    } else {
      analysisContent.classList.add('active');
      toggleBtn.textContent = '📋 Hide Analysis';
    }
  };

  window.copyCodeSnippet = function(differenceId) {
    const codeContent = document.getElementById(`code-${differenceId}`);
    const codeText = codeContent.textContent;
    
    // Use clipboard API if available
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(codeText).then(() => {
        showCopySuccess(differenceId);
      }).catch(() => {
        fallbackCopyTextToClipboard(codeText, differenceId);
      });
    } else {
      fallbackCopyTextToClipboard(codeText, differenceId);
    }
  };

  function fallbackCopyTextToClipboard(text, differenceId) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
      document.execCommand('copy');
      showCopySuccess(differenceId);
    } catch (err) {
      console.error('Fallback: Oops, unable to copy', err);
    }
    
    document.body.removeChild(textArea);
  }

  function showCopySuccess(differenceId) {
    const copyBtn = document.querySelector(`#code-${differenceId}`).parentElement.querySelector('.copy-code-btn');
    const originalText = copyBtn.textContent;
    
    copyBtn.textContent = '✓ Copied!';
    copyBtn.style.backgroundColor = '#4ecdc4';
    
    setTimeout(() => {
      copyBtn.textContent = originalText;
      copyBtn.style.backgroundColor = '#4ecdc4';
    }, 2000);
  }

  // Code Generation & Correction Functionality
  // Tab switching functionality
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  
  tabBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      const targetTab = this.getAttribute('data-tab');
      
      // Remove active class from all tabs and contents
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      
      // Add active class to clicked tab and corresponding content
      this.classList.add('active');
      document.getElementById(`${targetTab}-tab`).classList.add('active');
    });
  });
  
  // Generate Code Button
  const generateCodeBtn = document.getElementById('generate-code-btn');
  if (generateCodeBtn) {
    generateCodeBtn.addEventListener('click', generateCode);
  }
  
  // Correct Code Button
  const correctCodeBtn = document.getElementById('correct-code-btn');
  if (correctCodeBtn) {
    correctCodeBtn.addEventListener('click', correctCode);
  }
  
  // Copy Generated Code Button
  const copyGeneratedCodeBtn = document.getElementById('copy-generated-code');
  if (copyGeneratedCodeBtn) {
    copyGeneratedCodeBtn.addEventListener('click', () => copyCode('generated'));
  }
  
  // Copy Corrected Code Button
  const copyCorrectedCodeBtn = document.getElementById('copy-corrected-code');
  if (copyCorrectedCodeBtn) {
    copyCorrectedCodeBtn.addEventListener('click', () => copyCode('corrected'));
  }

  // Clear selected differences when starting new comparisons
  function clearSelectedDifferences() {
    selectedDifferences.clear();
    // Reset card styles
    document.querySelectorAll('.difference-card').forEach(card => {
      card.style.borderColor = '#4ecdc4';
      card.style.boxShadow = '0 0 15px rgba(78, 205, 196, 0.3)';
    });
    // Clear highlights
    updateComparisonHighlights();
  }

  // Mode switching and form submission handlers
  modeBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      // Remove active class from all buttons
      modeBtns.forEach(b => b.classList.remove('active'));
      // Add active class to clicked button
      this.classList.add('active');
      
      // Hide all sections
      const screenshotSection = document.getElementById('screenshot-comparison');
      const figmaSection = document.getElementById('figma-comparison');
      const comparisonSection = document.getElementById('comparison-images');
      const differencesSection = document.getElementById('detected-differences');
      const codeGenerationSection = document.getElementById('code-generation');
      
      if (screenshotSection) screenshotSection.style.display = 'none';
      if (figmaSection) figmaSection.style.display = 'none';
      if (comparisonSection) comparisonSection.style.display = 'none';
      if (differencesSection) differencesSection.style.display = 'none';
      if (codeGenerationSection) codeGenerationSection.style.display = 'none';
      
      // Show the appropriate section
      if (this.textContent.includes('Screenshot')) {
        if (screenshotSection) screenshotSection.style.display = 'block';
      } else {
        if (figmaSection) figmaSection.style.display = 'block';
      }
      
      // Clear any existing data
      clearSelectedDifferences();
    });
  });
});

// Code Generation & Correction Functions
async function generateCode() {
  const language = document.getElementById('language-select').value;
  const componentName = document.getElementById('component-name').value || 'Component';
  const requirements = document.getElementById('additional-requirements').value;
  const generateBtn = document.getElementById('generate-code-btn');
  const resultDiv = document.getElementById('generated-code-result');
  const codeContent = document.getElementById('generated-code-content');
  
  // Get session ID from the global scope
  const sessionId = window.currentSessionId;
  
  if (!sessionId) {
    alert('Please perform a comparison first to generate code.');
    return;
  }
  
  // Show loading state
  const originalText = generateBtn.textContent;
  generateBtn.innerHTML = '<span class="loading-spinner"></span>Generating Code...';
  generateBtn.disabled = true;
  
  try {
    const response = await fetch('/generate_code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        language: language,
        component_name: componentName,
        requirements: requirements,
        session_id: sessionId
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Display the generated code
      codeContent.innerHTML = `<pre>${escapeHtml(data.code)}</pre>`;
      resultDiv.style.display = 'block';
      resultDiv.scrollIntoView({ behavior: 'smooth' });
    } else {
      alert('Error generating code: ' + data.error);
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Error generating code. Please try again.');
  } finally {
    // Reset button state
    generateBtn.textContent = originalText;
    generateBtn.disabled = false;
  }
}

async function correctCode() {
  const language = document.getElementById('existing-language').value;
  const existingCode = document.getElementById('existing-code').value;
  const notes = document.getElementById('correction-notes').value;
  const correctBtn = document.getElementById('correct-code-btn');
  const resultDiv = document.getElementById('corrected-code-result');
  const codeContent = document.getElementById('corrected-code-content');
  const changesList = document.getElementById('correction-changes');
  
  // Get session ID from the global scope
  const sessionId = window.currentSessionId;
  
  if (!sessionId) {
    alert('Please perform a comparison first to correct code.');
    return;
  }
  
  if (!existingCode.trim()) {
    alert('Please paste your existing code to correct.');
    return;
  }
  
  // Show loading state
  const originalText = correctBtn.textContent;
  correctBtn.innerHTML = '<span class="loading-spinner"></span>Correcting Code...';
  correctBtn.disabled = true;
  
  try {
    const response = await fetch('/correct_code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        language: language,
        existing_code: existingCode,
        notes: notes,
        session_id: sessionId
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Display the corrected code
      codeContent.innerHTML = `<pre>${escapeHtml(data.corrected_code)}</pre>`;
      
      // Display changes made
      changesList.innerHTML = '';
      data.changes.forEach(change => {
        const li = document.createElement('li');
        li.textContent = change;
        changesList.appendChild(li);
      });
      
      resultDiv.style.display = 'block';
      resultDiv.scrollIntoView({ behavior: 'smooth' });
    } else {
      alert('Error correcting code: ' + data.error);
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Error correcting code. Please try again.');
  } finally {
    // Reset button state
    correctBtn.textContent = originalText;
    correctBtn.disabled = false;
  }
}

function copyCode(type) {
  const codeContent = document.getElementById(`${type}-code-content`);
  const copyBtn = document.getElementById(`copy-${type}-code`);
  
  if (!codeContent) return;
  
  const codeText = codeContent.textContent;
  
  // Use clipboard API if available
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(codeText).then(() => {
      showCopyCodeSuccess(copyBtn);
    }).catch(() => {
      fallbackCopyTextToClipboard(codeText, copyBtn);
    });
  } else {
    fallbackCopyTextToClipboard(codeText, copyBtn);
  }
}

function fallbackCopyTextToClipboard(text, copyBtn) {
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.left = '-999999px';
  textArea.style.top = '-999999px';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  
  try {
    document.execCommand('copy');
    showCopyCodeSuccess(copyBtn);
  } catch (err) {
    console.error('Fallback: Oops, unable to copy', err);
  }
  
  document.body.removeChild(textArea);
}

function showCopyCodeSuccess(copyBtn) {
  const originalText = copyBtn.textContent;
  
  copyBtn.textContent = '✓ Copied!';
  copyBtn.style.backgroundColor = '#4ecdc4';
  
  setTimeout(() => {
    copyBtn.textContent = originalText;
    copyBtn.style.backgroundColor = '#ffa500';
  }, 2000);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Function to generate a unique session ID
function generateSessionId() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    var r = (Math.random() * 16) | 0,
      v = c == "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// Issue Selection Functions
function selectIssue(issueId, action) {
  issueSelections[issueId] = action;
  updateIssueCard(issueId, action);
  updateSelectionCounts();
}

function updateIssueCard(issueId, action) {
  const card = document.querySelector(`[data-issue-id="${issueId}"]`);
  if (card) {
    const keepBtn = card.querySelector('.keep-btn');
    const neglectBtn = card.querySelector('.neglect-btn');
    
    if (action === 'keep') {
      keepBtn.classList.add('active');
      neglectBtn.classList.remove('active');
      card.classList.remove('neglected');
      card.classList.add('selected');
    } else {
      neglectBtn.classList.add('active');
      keepBtn.classList.remove('active');
      card.classList.remove('selected');
      card.classList.add('neglected');
    }
  }
}

function updateSelectionCounts() {
  const selectedCount = Object.values(issueSelections).filter(v => v === 'keep').length;
  const neglectedCount = Object.values(issueSelections).filter(v => v === 'neglect').length;
  
  const selectedCountElement = document.getElementById('selected-count');
  const neglectedCountElement = document.getElementById('neglected-count');
  
  if (selectedCountElement) selectedCountElement.textContent = selectedCount;
  if (neglectedCountElement) neglectedCountElement.textContent = neglectedCount;
}

function selectAllIssues() {
  document.querySelectorAll('[data-issue-id]').forEach(card => {
    const issueId = parseInt(card.getAttribute('data-issue-id'));
    selectIssue(issueId, 'keep');
  });
}

function neglectAllIssues() {
  document.querySelectorAll('[data-issue-id]').forEach(card => {
    const issueId = parseInt(card.getAttribute('data-issue-id'));
    selectIssue(issueId, 'neglect');
  });
}

async function saveIssueSelections() {
  const sessionId = window.currentSessionId;
  if (!sessionId) {
    alert('No active session. Please perform a comparison first.');
    return;
  }
  
  try {
    const response = await fetch('/select_issues', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        selections: issueSelections
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      showTestResult('Issue selections saved successfully! Sorting display...', 'success');
      
      // Sort and redisplay issues (kept first, then neglected)
      sortAndRedisplayIssues();
    } else {
      showTestResult('Failed to save selections: ' + result.error, 'error');
    }
  } catch (error) {
    showTestResult('Error saving selections: ' + error.message, 'error');
  }
}

function sortAndRedisplayIssues() {
  const differencesGrid = document.getElementById("differences-grid");
  const allCards = document.querySelectorAll('[data-issue-id]');
  
  // Separate kept and neglected issues
  const keptCards = [];
  const neglectedCards = [];
  
  allCards.forEach(card => {
    const issueId = parseInt(card.getAttribute('data-issue-id'));
    const selection = issueSelections[issueId];
    
    if (selection === 'keep') {
      keptCards.push(card);
    } else {
      neglectedCards.push(card);
    }
  });
  
  // Remove all cards from the grid
  allCards.forEach(card => {
    if (card.parentNode) {
      card.parentNode.removeChild(card);
    }
  });
  
  // Remove the selection controls
  const selectionControls = differencesGrid.querySelector('.issue-selection-controls');
  if (selectionControls) {
    selectionControls.remove();
  }
  
  // Add sorted sections
  addSortedSections(differencesGrid, keptCards, neglectedCards);
  
  // Update display information
  updateDisplayForSortedIssues(keptCards.length, neglectedCards.length);
}

function addSortedSections(differencesGrid, keptCards, neglectedCards) {
  // Add "Selections Saved" indicator
  const savedIndicator = document.createElement('div');
  savedIndicator.className = 'selections-saved-indicator';
  savedIndicator.innerHTML = `
    <div class="saved-message">
      ✅ Selections saved! Issues sorted by priority and category
      <button class="reset-selections-btn" onclick="resetToAllIssues()">🔄 Reset to All Issues</button>
    </div>
  `;
  differencesGrid.appendChild(savedIndicator);
  
  // Add Kept Issues Section with Categories
  if (keptCards.length > 0) {
    const keptSection = document.createElement('div');
    keptSection.className = 'issues-section kept-section';
    keptSection.innerHTML = `
      <div class="section-header kept-header">
        <h3>✅ Issues to Keep (${keptCards.length})</h3>
        <p>These issues will be used for code correction</p>
      </div>
    `;
    differencesGrid.appendChild(keptSection);
    
    // Group kept cards by category
    const keptByCategory = groupCardsByCategory(keptCards);
    
    // Add Metadata Issues first (complete list)
    if (keptByCategory['metadata-issues'] && keptByCategory['metadata-issues'].length > 0) {
      addCategorySubsection(keptSection, 'Metadata Issues', keptByCategory['metadata-issues'], 'kept');
    }
    
    // Add Content Issues (complete list)
    if (keptByCategory['content-issues'] && keptByCategory['content-issues'].length > 0) {
      addCategorySubsection(keptSection, 'Content Issues', keptByCategory['content-issues'], 'kept');
    }
  }
  
  // Add Neglected Issues Section with Categories
  if (neglectedCards.length > 0) {
    const neglectedSection = document.createElement('div');
    neglectedSection.className = 'issues-section neglected-section';
    neglectedSection.innerHTML = `
      <div class="section-header neglected-header">
        <h3>❌ Neglected Issues (${neglectedCards.length})</h3>
        <p>These issues will be ignored during code correction</p>
      </div>
    `;
    differencesGrid.appendChild(neglectedSection);
    
    // Group neglected cards by category
    const neglectedByCategory = groupCardsByCategory(neglectedCards);
    
    // Add Metadata Issues first (complete list)
    if (neglectedByCategory['metadata-issues'] && neglectedByCategory['metadata-issues'].length > 0) {
      addCategorySubsection(neglectedSection, 'Metadata Issues', neglectedByCategory['metadata-issues'], 'neglected');
    }
    
    // Add Content Issues (complete list)
    if (neglectedByCategory['content-issues'] && neglectedByCategory['content-issues'].length > 0) {
      addCategorySubsection(neglectedSection, 'Content Issues', neglectedByCategory['content-issues'], 'neglected');
    }
  }
}

function groupCardsByCategory(cards) {
  const grouped = {};
  
  cards.forEach(card => {
    const categoryElement = card.querySelector('.issue-category');
    if (categoryElement) {
      const category = categoryElement.textContent.trim();
      const categoryKey = category.toLowerCase().replace(' ', '-');
      
      if (!grouped[categoryKey]) {
        grouped[categoryKey] = [];
      }
      grouped[categoryKey].push(card);
    } else {
      // Default to content-issues if no category found
      if (!grouped['content-issues']) {
        grouped['content-issues'] = [];
      }
      grouped['content-issues'].push(card);
    }
  });
  
  return grouped;
}

function addCategorySubsection(parentSection, categoryName, cards, status) {
  const subsection = document.createElement('div');
  subsection.className = `category-subsection ${status}-${categoryName.toLowerCase().replace(' ', '-')}`;
  subsection.innerHTML = `
    <div class="category-subheader ${status}-subheader">
      <h4>${categoryName} (${cards.length})</h4>
    </div>
    <div class="issue-cards-container">
    </div>
  `;
  
  // Add cards to the container
  const container = subsection.querySelector('.issue-cards-container');
  cards.forEach(card => {
    container.appendChild(card);
  });
  
  parentSection.appendChild(subsection);
}

function updateDisplayForSortedIssues(keptCount, neglectedCount) {
  const differencesSection = document.getElementById("detected-differences");
  const totalDifferencesSpan = document.getElementById("total-differences");
  
  // Update total count
  totalDifferencesSpan.textContent = keptCount + neglectedCount;
  
  // Update the summary text
  const summaryElement = differencesSection.querySelector('.differences-summary p');
  if (summaryElement) {
    summaryElement.innerHTML = `Total differences found: <span id="total-differences">${keptCount + neglectedCount}</span> (${keptCount} kept, ${neglectedCount} neglected)`;
  }
  
  // Update the differences title
  const differencesTitle = differencesSection.querySelector('.differences-title');
  if (differencesTitle) {
    differencesTitle.textContent = `Issues Sorted by Priority (${keptCount} kept, ${neglectedCount} neglected)`;
  }
  
  // Show success message
  showTestResult(`Issues sorted! ${keptCount} kept issues will be used for code correction.`, 'success');
}

// Old filter function removed - replaced with sortAndRedisplayIssues

// Old update function removed - replaced with updateDisplayForSortedIssues

function resetToAllIssues() {
  // Reload the page to show all issues again
  location.reload();
}

// Initialize selections when differences are displayed
function initializeIssueSelections(differences) {
  issueSelections = {};
  differences.forEach(diff => {
    issueSelections[diff.id] = 'keep'; // Default to keep
  });
  updateSelectionCounts();
} 