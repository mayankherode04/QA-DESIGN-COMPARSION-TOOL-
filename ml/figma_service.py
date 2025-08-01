import requests
import base64
import io
from PIL import Image
import os
from datetime import datetime


class FigmaService:
    """Service class to interact with Figma API"""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.figma.com/v1"
        self.headers = {
            "X-Figma-Token": access_token
        }
    
    def validate_token(self):
        """Validate the Figma access token"""
        try:
            response = requests.get(f"{self.base_url}/me", headers=self.headers)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Invalid token: {response.status_code} - {response.text}"
        except Exception as e:
            return False, f"Error validating token: {str(e)}"
    
    def get_file_info(self, file_key):
        """Get information about a Figma file"""
        try:
            response = requests.get(f"{self.base_url}/files/{file_key}", headers=self.headers)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Error fetching file: {response.status_code} - {response.text}"
        except Exception as e:
            return False, f"Error getting file info: {str(e)}"
    
    def get_node_info(self, file_key, node_id):
        """Get information about a specific node in the file"""
        try:
            response = requests.get(f"{self.base_url}/files/{file_key}/nodes?ids={node_id}", headers=self.headers)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Error fetching node: {response.status_code} - {response.text}"
        except Exception as e:
            return False, f"Error getting node info: {str(e)}"
    
    def export_image(self, file_key, node_id=None, format="png", scale=2):
        """Export an image from Figma"""
        try:
            # Clean and validate file key
            file_key = file_key.strip()
            if not file_key:
                return False, "File key is empty"
            
            # Build the export URL
            if node_id:
                node_id = node_id.strip()
                if not node_id:
                    return False, "Node ID is empty"
                url = f"{self.base_url}/images/{file_key}?ids={node_id}&format={format}&scale={scale}"
                # Exporting node
            else:
                # For entire file export, we need to get the main frame first
                # Exporting entire file
                file_success, file_info = self.get_file_info(file_key)
                if not file_success:
                    return False, f"Could not access file: {file_info}"
                
                # Get the first page and its first frame
                if 'document' in file_info and 'children' in file_info['document']:
                    pages = file_info['document']['children']
                    if pages:
                        first_page = pages[0]
                        if 'children' in first_page and first_page['children']:
                            first_frame = first_page['children'][0]
                            node_id = first_frame['id']
                            url = f"{self.base_url}/images/{file_key}?ids={node_id}&format={format}&scale={scale}"
                            # Using first frame
                        else:
                            return False, "No frames found in the first page"
                    else:
                        return False, "No pages found in the file"
                else:
                    return False, "Invalid file structure"
            
            # Making API request
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except Exception as json_error:
                    # Error parsing JSON response
                    return False, f"Invalid JSON response from Figma API: {str(json_error)}"
                
                if 'images' in data and data['images']:
                    image_url = list(data['images'].values())[0]
                    if image_url:
                        return self._download_image(image_url)
                    else:
                        return False, "No image URL returned - the node might not be exportable"
                else:
                    error_msg = data.get('err', 'Unknown error') if isinstance(data, dict) else 'No images found in response'
                    return False, f"Figma API error: {error_msg}"
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_data.get('err', 'Unknown error'))
                except:
                    error_msg = response.text if response.text else "No error details"
                return False, f"Error exporting image: HTTP {response.status_code} - {error_msg}"
        except Exception as e:
            return False, f"Error exporting image: {str(e)}"
    
    def _download_image(self, image_url):
        """Download image from URL and convert to PIL Image"""
        try:
            # Downloading image
            response = requests.get(image_url, timeout=30)
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                
                # Validate content length
                content_length = len(response.content)
                
                if content_length == 0:
                    return False, "Downloaded image is empty (0 bytes)"
                
                # Check if content looks like an image
                if not content_type.startswith('image/'):
                    # Try to detect image format from first few bytes
                    first_bytes = response.content[:10]
                
                # Try to open the image
                try:
                    image = Image.open(io.BytesIO(response.content))
                    # Force image to load to catch any errors
                    image.load()
                    return True, image
                except Exception as img_error:
                    # Try to save the raw content for debugging
                    try:
                        debug_path = "debug_downloaded_image.bin"
                        with open(debug_path, 'wb') as f:
                            f.write(response.content)
                    except:
                        pass
                    return False, f"Error opening image with PIL: {str(img_error)}"
            else:
                error_text = response.text if response.text else "No error details"
                return False, f"Error downloading image: HTTP {response.status_code} - {error_text}"
        except requests.exceptions.Timeout:
            return False, "Timeout while downloading image"
        except requests.exceptions.RequestException as e:
            return False, f"Network error downloading image: {str(e)}"
        except Exception as e:
            return False, f"Error downloading image: {str(e)}"
    
    def save_image(self, image, output_path):
        """Save PIL Image to file"""
        try:
            image.save(output_path, "PNG")
            return True, output_path
        except Exception as e:
            return False, f"Error saving image: {str(e)}"


def fetch_figma_design(access_token, file_key, node_id=None, output_dir=None):
    """
    Fetch a design from Figma and save it as an image
    
    Args:
        access_token (str): Figma access token
        file_key (str): Figma file key
        node_id (str, optional): Specific node ID to export
        output_dir (str, optional): Directory to save the image
        
    Returns:
        tuple: (success: bool, result: str or PIL.Image)
    """
    try:
        # Initialize Figma service
        figma_service = FigmaService(access_token)
        
        # Validate token
        is_valid, token_result = figma_service.validate_token()
        if not is_valid:
            return False, f"Token validation failed: {token_result}"
        
        # Get file info
        file_success, file_info = figma_service.get_file_info(file_key)
        if not file_success:
            return False, f"File access failed: {file_info}"
        
        # Export image
        export_success, export_result = figma_service.export_image(file_key, node_id)
        if not export_success:
            error_msg = f"Image export failed: {export_result}"
            return False, error_msg
        
        # Validate the exported result
        if not isinstance(export_result, Image.Image):
            error_msg = f"Invalid export result type: {type(export_result)}. Expected PIL.Image"
            return False, error_msg
        
        # Save image if output directory is provided
        if output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"figma_design_{timestamp}.png"
            output_path = os.path.join(output_dir, filename)
            
            save_success, save_result = figma_service.save_image(export_result, output_path)
            if save_success:
                return True, output_path
            else:
                error_msg = f"Failed to save image: {save_result}"
                return False, error_msg
        
        return True, export_result
        
    except Exception as e:
        return False, f"Error fetching Figma design: {str(e)}" 