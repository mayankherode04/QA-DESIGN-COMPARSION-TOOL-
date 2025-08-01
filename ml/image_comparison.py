import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from datetime import datetime
import os


def analyze_issue_type(figma_region, built_region, area, x, y, w, h):
    """
    Analyze the type of issue and provide detailed explanation and fix suggestions.
    
    Args:
        figma_region: Grayscale region from Figma image
        built_region: Grayscale region from built image
        area: Area of the difference
        x, y, w, h: Coordinates and dimensions
        
    Returns:
        dict: Issue analysis with explanation and code snippets
    """
    figma_mean = np.mean(figma_region)
    built_mean = np.mean(built_region)
    
    # Calculate additional metrics
    figma_std = np.std(figma_region)
    built_std = np.std(built_region)
    
    # Determine issue type and provide detailed analysis
    if figma_mean > built_mean + 30:  # Much brighter in Figma
        if area > 1000:
            return {
                'issue_type': 'Missing UI Component',
                'issue_category': 'Content Issues',
                'explanation': f'A large UI component (area: {area}px²) is present in the design but missing in the implementation. This could be a button, card, section, or other major UI element.',
                'severity': 'High',
                'code_snippet': f'''<!-- Add the missing component at position ({x}, {y}) -->
<div class="missing-component" style="width: {w}px; height: {h}px;">
    <!-- Replace with actual component content -->
    <button class="btn btn-primary">Missing Button</button>
</div>

/* CSS for the missing component */
.missing-component {{
    position: absolute;
    left: {x}px;
    top: {y}px;
    width: {w}px;
    height: {h}px;
}}''',
                'fix_steps': [
                    'Identify the missing component from the design',
                    'Add the component to the HTML structure',
                    'Apply appropriate styling to match the design',
                    'Ensure proper positioning and dimensions'
                ]
            }
        else:
            return {
                'issue_type': 'Missing Small Element',
                'issue_category': 'Content Issues',
                'explanation': f'A small UI element (area: {area}px²) is missing from the implementation. This could be an icon, text, or decorative element.',
                'severity': 'Medium',
                'code_snippet': f'''<!-- Add the missing small element -->
<span class="missing-element" style="width: {w}px; height: {h}px;">
    <!-- Replace with actual element (icon, text, etc.) -->
    <i class="icon-missing"></i>
</span>

/* CSS for the missing element */
.missing-element {{
    position: absolute;
    left: {x}px;
    top: {y}px;
    width: {w}px;
    height: {h}px;
    display: flex;
    align-items: center;
    justify-content: center;
}}''',
                'fix_steps': [
                    'Identify the missing element from the design',
                    'Add the element to the appropriate container',
                    'Apply correct positioning and styling',
                    'Ensure the element is visible and accessible'
                ]
            }
    elif built_mean > figma_mean + 30:  # Much brighter in built
        if area > 1000:
            return {
                'issue_type': 'Extra UI Component',
                'issue_category': 'Content Issues',
                'explanation': f'An extra UI component (area: {area}px²) is present in the implementation but not in the design. This should be removed or hidden.',
                'severity': 'High',
                'code_snippet': f'''<!-- Remove or hide the extra component -->
<!-- Find and remove this component from your HTML -->
<div class="extra-component" style="display: none;">
    <!-- This component should not be here -->
</div>

/* CSS to hide the extra component */
.extra-component {{
    display: none !important;
    /* Or use: visibility: hidden; */
}}''',
                'fix_steps': [
                    'Identify the extra component in the implementation',
                    'Remove it from the HTML structure if not needed',
                    'Or hide it with CSS if it might be needed later',
                    'Update any related JavaScript functionality'
                ]
            }
        else:
            return {
                'issue_type': 'Extra Small Element',
                'issue_category': 'Content Issues',
                'explanation': f'An extra small element (area: {area}px²) is present in the implementation but not in the design.',
                'severity': 'Medium',
                'code_snippet': f'''<!-- Remove or hide the extra element -->
<!-- Find and remove this element -->
<span class="extra-element" style="display: none;">
    <!-- This element should not be here -->
</span>

/* CSS to hide the extra element */
.extra-element {{
    display: none !important;
}}''',
                'fix_steps': [
                    'Identify the extra element in the implementation',
                    'Remove it from the HTML if not needed',
                    'Or hide it with CSS',
                    'Check if it affects layout or functionality'
                ]
            }
    else:  # Similar brightness but different structure
        # Determine if it's a metadata issue based on area and position
        if area < 500 and (w < 50 or h < 50):
            # Small differences are likely metadata issues (spacing, alignment, etc.)
            return {
                'issue_type': 'Spacing/Alignment Issue',
                'issue_category': 'Metadata Issues',
                'explanation': f'A spacing or alignment issue detected (area: {area}px²). This is likely a minor positioning or spacing problem.',
                'severity': 'Low',
                'code_snippet': f'''/* Fix spacing/alignment issue */
.element {{
    margin: 0;
    padding: 0;
    /* Adjust spacing as needed */
    margin-left: {x}px;
    margin-top: {y}px;
}}

/* Or use flexbox for better alignment */
.container {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}}''',
                'fix_steps': [
                    'Check spacing between elements',
                    'Adjust margins and padding',
                    'Use flexbox or grid for alignment',
                    'Ensure consistent spacing throughout'
                ]
            }
        elif area > 2000 and abs(figma_std - built_std) > 10:
            # Large differences with high variance are likely layout issues
            return {
                'issue_type': 'Layout/Positioning Issue',
                'issue_category': 'Metadata Issues',
                'explanation': f'A layout or positioning issue detected (area: {area}px²). The element exists but is positioned or sized incorrectly.',
                'severity': 'Medium',
                'code_snippet': f'''/* Fix the positioning/sizing issue */
.component {{
    position: absolute;
    left: {x}px;
    top: {y}px;
    width: {w}px;
    height: {h}px;
    /* Ensure proper positioning */
    z-index: 1;
}}

/* Alternative: Use flexbox/grid for better layout */
.container {{
    display: flex;
    align-items: center;
    justify-content: center;
}}''',
                'fix_steps': [
                    'Check the element\'s positioning in the design',
                    'Update CSS positioning properties',
                    'Verify dimensions match the design',
                    'Test on different screen sizes'
                ]
            }
        else:
            # Default case for other structural differences
            return {
                'issue_type': 'Visual Inconsistency',
                'issue_category': 'Metadata Issues',
                'explanation': f'A visual inconsistency detected (area: {area}px²). The element may have different styling, colors, or visual properties.',
                'severity': 'Medium',
                'code_snippet': f'''/* Fix visual inconsistency */
.element {{
    /* Check and update these properties */
    background-color: #correct-color;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    font-size: 14px;
    line-height: 1.5;
}}''',
                'fix_steps': [
                    'Compare visual properties with design',
                    'Update colors, fonts, and styling',
                    'Check for missing CSS properties',
                    'Ensure consistent visual appearance'
                ]
            }


def compare_images(figma_path, built_path, output_dir):
    """
    Compare two images and generate a comparison result with similarity score.
    
    Args:
        figma_path (str): Path to the Figma design image
        built_path (str): Path to the built screen image
        output_dir (str): Directory to save the comparison image
        
    Returns:
        dict: Comparison result with similarity score, message, comparison image path, and detected differences
    """
    # Read images
    figma_img = cv2.imread(figma_path)
    built_img = cv2.imread(built_path)

    # Ensure images are the same size
    figma_img = cv2.resize(figma_img, (built_img.shape[1], built_img.shape[0]))

    # Convert images to grayscale
    figma_gray = cv2.cvtColor(figma_img, cv2.COLOR_BGR2GRAY)
    built_gray = cv2.cvtColor(built_img, cv2.COLOR_BGR2GRAY)

    # Compute SSIM between the two images
    (score, diff) = ssim(figma_gray, built_gray, full=True)

    # The diff image contains the actual image differences
    diff = (diff * 255).astype("uint8")

    # Threshold the difference image, followed by finding contours
    thresh = cv2.threshold(
        diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    contours = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    # Create a mask image that we will use to visualize the differences
    mask = np.zeros(figma_img.shape, dtype='uint8')
    filled_after = figma_img.copy()

    # Create copies for individual images
    figma_with_boxes = figma_img.copy()
    built_with_boxes = built_img.copy()

    # List to store detected differences
    detected_differences = []

    for i, c in enumerate(contours):
        area = cv2.contourArea(c)
        if area > 40:
            x, y, w, h = cv2.boundingRect(c)
            
            # Draw rectangles on both images
            figma_with_boxes = cv2.rectangle(
                figma_with_boxes, (x, y), (x + w, y + h), (0, 255, 0), 2)
            built_with_boxes = cv2.rectangle(
                built_with_boxes, (x, y), (x + w, y + h), (0, 0, 255), 2)

            # Compare the region in both images
            figma_region = figma_gray[y:y+h, x:x+w]
            built_region = built_gray[y:y+h, x:x+w]

            # Calculate region statistics
            figma_mean = np.mean(figma_region)
            built_mean = np.mean(built_region)
            
            # Determine difference type based on brightness
            if figma_mean > built_mean:
                # More white in Figma, use green
                cv2.drawContours(filled_after, [c], 0, (0, 255, 0), -1)
                difference_type = "Missing Element"
                description = "Element present in design but missing in implementation"
            else:
                # More white in built, use red
                cv2.drawContours(filled_after, [c], 0, (0, 0, 255), -1)
                difference_type = "Extra Element"
                description = "Element present in implementation but not in design"

            # Analyze the issue in detail
            issue_analysis = analyze_issue_type(figma_region, built_region, area, x, y, w, h)

            # Add difference information
            detected_differences.append({
                'id': i + 1,
                'type': difference_type,
                'description': description,
                'location': f"({x}, {y})",
                'size': f"{w} × {h}",
                'area': int(area),
                'severity': 'High' if area > 1000 else 'Medium' if area > 200 else 'Low',
                'coordinates': {
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h
                },
                'issue_analysis': issue_analysis
            })

    # Create the comparison image
    comparison = np.hstack((figma_with_boxes, built_with_boxes, filled_after))

    # Generate filenames with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save individual images
    figma_filename = f'figma_annotated_{timestamp}.jpg'
    built_filename = f'built_annotated_{timestamp}.jpg'
    difference_filename = f'difference_map_{timestamp}.jpg'
    comparison_filename = f'comparison_{timestamp}.jpg'
    
    figma_path_saved = os.path.join(output_dir, figma_filename)
    built_path_saved = os.path.join(output_dir, built_filename)
    difference_path_saved = os.path.join(output_dir, difference_filename)
    comparison_path = os.path.join(output_dir, comparison_filename)
    
    # Save all images
    cv2.imwrite(figma_path_saved, figma_with_boxes)
    cv2.imwrite(built_path_saved, built_with_boxes)
    cv2.imwrite(difference_path_saved, filled_after)
    cv2.imwrite(comparison_path, comparison)

    return {
        'similarity': f'{score * 100:.2f}',
        'message': f'The images are {score * 100:.2f}% similar based on structural similarity.',
        'comparison_image': comparison_path,
        'figma_image': figma_path_saved,
        'built_image': built_path_saved,
        'difference_image': difference_path_saved,
        'detected_differences': detected_differences,
        'total_differences': len(detected_differences)
    } 