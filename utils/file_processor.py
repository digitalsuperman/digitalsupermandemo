"""
File processor utility to handle various file formats
"""

import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any
from PIL import Image
import PyPDF2
import zipfile
import tempfile
import hashlib

class FileProcessor:
    def __init__(self):
        self.supported_formats = {
            '.png': self._process_image,
            '.jpg': self._process_image,
            '.jpeg': self._process_image,
            '.pdf': self._process_pdf,
            '.xml': self._process_xml,
            '.drawio': self._process_drawio,
            '.vsdx': self._process_vsdx,
            '.svg': self._process_svg
        }
        
        # File content cache
        self._file_cache = {}
        self._max_cache_size = 20
    
    def _get_file_cache_key(self, filepath):
        """Generate cache key based on file path and modification time"""
        stat = os.stat(filepath)
        return hashlib.md5(f"{filepath}{stat.st_mtime}{stat.st_size}".encode()).hexdigest()
    
    def _get_from_cache(self, cache_key):
        """Get cached file content"""
        return self._file_cache.get(cache_key)
    
    def _save_to_cache(self, cache_key, content):
        """Save file content to cache"""
        if len(self._file_cache) >= self._max_cache_size:
            oldest_key = next(iter(self._file_cache))
            del self._file_cache[oldest_key]
        self._file_cache[cache_key] = content

    def process_file(self, filepath: str) -> Dict[str, Any]:
        """Process uploaded file and extract relevant content"""
        try:
            file_extension = os.path.splitext(filepath)[1].lower()
            
            if file_extension not in self.supported_formats:
                return {
                    'error': f'Unsupported file format: {file_extension}',
                    'type': 'unsupported',
                    'text': '',
                    'metadata': {}
                }
            
            # Check cache first
            cache_key = self._get_file_cache_key(filepath)
            cached_content = self._get_from_cache(cache_key)
            if cached_content:
                print(f"📁 File Processor: Using cached content for {os.path.basename(filepath)}")
                return cached_content
            
            # Process file based on extension
            processor = self.supported_formats[file_extension]
            result = processor(filepath)
            
            # Add common metadata
            result['metadata'].update({
                'filename': os.path.basename(filepath),
                'file_size': os.path.getsize(filepath),
                'file_extension': file_extension,
                'processed_timestamp': self._get_timestamp()
            })
            
            # Save to cache
            self._save_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            return {
                'error': f'Error processing file: {str(e)}',
                'type': 'error',
                'text': '',
                'metadata': {'filename': os.path.basename(filepath)}
            }
    
    def _process_image(self, filepath: str) -> Dict[str, Any]:
        """Process image files (PNG, JPG, JPEG)"""
        try:
            with Image.open(filepath) as img:
                # Extract image metadata
                metadata = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode
                }
                
                # Try to extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    metadata['exif'] = dict(img._getexif())
                
                return {
                    'type': 'image',
                    'text': f'Image file: {img.format} format, {img.width}x{img.height} pixels',
                    'metadata': metadata,
                    'image_path': filepath
                }
        except Exception as e:
            return {
                'type': 'image',
                'text': f'Error processing image: {str(e)}',
                'metadata': {},
                'error': str(e)
            }
    
    def _process_pdf(self, filepath: str) -> Dict[str, Any]:
        """Process PDF files"""
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                text_content = []
                for page_num, page in enumerate(pdf_reader.pages):
                    text_content.append(f"Page {page_num + 1}: {page.extract_text()}")
                
                metadata = {
                    'num_pages': len(pdf_reader.pages),
                    'title': pdf_reader.metadata.get('/Title', 'Unknown') if pdf_reader.metadata else 'Unknown',
                    'author': pdf_reader.metadata.get('/Author', 'Unknown') if pdf_reader.metadata else 'Unknown',
                    'creator': pdf_reader.metadata.get('/Creator', 'Unknown') if pdf_reader.metadata else 'Unknown'
                }
                
                return {
                    'type': 'pdf',
                    'text': '\n'.join(text_content),
                    'metadata': metadata
                }
        except Exception as e:
            return {
                'type': 'pdf',
                'text': f'Error processing PDF: {str(e)}',
                'metadata': {},
                'error': str(e)
            }
    
    def _process_xml(self, filepath: str) -> Dict[str, Any]:
        """Process XML files"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Parse XML
            root = ET.fromstring(content)
            
            # Extract text content and structure
            text_content = self._extract_xml_text(root)
            
            metadata = {
                'root_tag': root.tag,
                'namespace': root.tag.split('}')[0][1:] if '}' in root.tag else None,
                'element_count': len(list(root.iter()))
            }
            
            return {
                'type': 'xml',
                'text': text_content,
                'metadata': metadata,
                'xml_content': content
            }
        except Exception as e:
            return {
                'type': 'xml',
                'text': f'Error processing XML: {str(e)}',
                'metadata': {},
                'error': str(e)
            }
    
    def _process_drawio(self, filepath: str) -> Dict[str, Any]:
        """Process Draw.io files"""
        try:
            # Draw.io files are compressed XML
            with zipfile.ZipFile(filepath, 'r') as zip_file:
                # Look for diagram files
                diagram_files = [f for f in zip_file.namelist() if f.endswith('.xml')]
                
                if not diagram_files:
                    # If no XML files, try to read as uncompressed XML
                    return self._process_xml(filepath)
                
                # Extract and process the main diagram
                main_diagram = diagram_files[0]
                with zip_file.open(main_diagram) as xml_file:
                    xml_content = xml_file.read().decode('utf-8')
                
                # Parse the XML content
                root = ET.fromstring(xml_content)
                text_content = self._extract_drawio_content(root)
                
                metadata = {
                    'diagram_files': diagram_files,
                    'main_diagram': main_diagram,
                    'is_compressed': True
                }
                
                return {
                    'type': 'drawio',
                    'text': text_content,
                    'metadata': metadata,
                    'xml_content': xml_content
                }
        except zipfile.BadZipFile:
            # Try processing as regular XML
            return self._process_xml(filepath)
        except Exception as e:
            return {
                'type': 'drawio',
                'text': f'Error processing Draw.io file: {str(e)}',
                'metadata': {},
                'error': str(e)
            }
    
    def _process_vsdx(self, filepath: str) -> Dict[str, Any]:
        """Process Visio files"""
        try:
            with zipfile.ZipFile(filepath, 'r') as zip_file:
                # Look for content files
                content_files = [f for f in zip_file.namelist() if 'content' in f.lower()]
                
                extracted_content = []
                for content_file in content_files:
                    try:
                        with zip_file.open(content_file) as cf:
                            content = cf.read().decode('utf-8')
                            extracted_content.append(content)
                    except:
                        continue
                
                metadata = {
                    'content_files': content_files,
                    'file_count': len(zip_file.namelist())
                }
                
                return {
                    'type': 'vsdx',
                    'text': '\n'.join(extracted_content),
                    'metadata': metadata
                }
        except Exception as e:
            return {
                'type': 'vsdx',
                'text': f'Error processing VSDX file: {str(e)}',
                'metadata': {},
                'error': str(e)
            }
    
    def _process_svg(self, filepath: str) -> Dict[str, Any]:
        """Process SVG files"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Parse SVG
            root = ET.fromstring(content)
            
            # Extract text content
            text_content = self._extract_svg_text(root)
            
            # Extract SVG metadata
            metadata = {
                'width': root.get('width', 'Unknown'),
                'height': root.get('height', 'Unknown'),
                'viewBox': root.get('viewBox', 'Unknown'),
                'element_count': len(list(root.iter()))
            }
            
            return {
                'type': 'svg',
                'text': text_content,
                'metadata': metadata,
                'svg_content': content
            }
        except Exception as e:
            return {
                'type': 'svg',
                'text': f'Error processing SVG: {str(e)}',
                'metadata': {},
                'error': str(e)
            }
    
    def _extract_xml_text(self, element) -> str:
        """Extract text content from XML element"""
        text_parts = []
        
        # Add element tag and attributes
        if element.tag:
            text_parts.append(f"Element: {element.tag}")
        
        if element.attrib:
            text_parts.append(f"Attributes: {element.attrib}")
        
        # Add text content
        if element.text and element.text.strip():
            text_parts.append(f"Text: {element.text.strip()}")
        
        # Recursively process children
        for child in element:
            text_parts.append(self._extract_xml_text(child))
        
        return '\n'.join(text_parts)
    
    def _extract_drawio_content(self, root) -> str:
        """Extract content from Draw.io XML"""
        text_parts = []
        
        # Look for mxCell elements which contain the diagram content
        for cell in root.iter():
            if 'mxCell' in cell.tag:
                # Extract cell attributes
                if cell.attrib:
                    text_parts.append(f"Cell: {cell.attrib}")
            
            # Extract text content
            if cell.text and cell.text.strip():
                text_parts.append(f"Text: {cell.text.strip()}")
        
        return '\n'.join(text_parts)
    
    def _extract_svg_text(self, element) -> str:
        """Extract text content from SVG element"""
        text_parts = []
        
        # Look for text elements
        for text_elem in element.iter():
            if text_elem.tag.endswith('text') or text_elem.tag.endswith('title'):
                if text_elem.text and text_elem.text.strip():
                    text_parts.append(text_elem.text.strip())
        
        return '\n'.join(text_parts)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
