"""
Config file parser for Codebase Atlas.

Handles JSON and YAML configuration files.
"""

import json
import yaml
from typing import Any, List
from .base_parser import BaseParser
from ..models import FileInfo
from ..config import AtlasConfig, CONFIG_EXTENSIONS


class ConfigParser(BaseParser):
    """Parser for JSON and YAML configuration files."""
    
    def can_parse(self, file_info: FileInfo) -> bool:
        """Check if this is a config file."""
        return file_info.ext in CONFIG_EXTENSIONS
    
    def parse(self, file_info: FileInfo) -> FileInfo:
        """
        Parse configuration file.
        
        Args:
            file_info: File to parse
        
        Returns:
            FileInfo with config keys extracted
        """
        # Read file content
        content = self.read_file_content(file_info)
        if content is None:
            return file_info
        
        file_info.loc = self.count_loc(content)
        
        # Parse based on extension
        try:
            if file_info.ext == '.json':
                data = self._parse_json(content)
            else:  # .yaml or .yml
                data = self._parse_yaml(content)
            
            # Extract keys
            file_info.config_keys = self._extract_keys(data)
            
        except json.JSONDecodeError as e:
            file_info.error = f"JSON parse error: {str(e)}"
        except yaml.YAMLError as e:
            file_info.error = f"YAML parse error: {str(e)}"
        except Exception as e:
            file_info.error = f"Config parse error: {str(e)}"
        
        return file_info
    
    def _parse_json(self, content: str) -> Any:
        """
        Parse JSON content.
        
        Args:
            content: JSON string
        
        Returns:
            Parsed data
        """
        return json.loads(content)
    
    def _parse_yaml(self, content: str) -> Any:
        """
        Parse YAML content.
        
        Args:
            content: YAML string
        
        Returns:
            Parsed data
        """
        return yaml.safe_load(content)
    
    def _extract_keys(self, data: Any, prefix: str = '', max_depth: int = 3) -> List[str]:
        """
        Extract keys from parsed config data.
        
        Recursively extracts keys up to max_depth levels.
        
        Args:
            data: Parsed data
            prefix: Key prefix for nested keys
            max_depth: Maximum nesting depth
        
        Returns:
            List of key paths (e.g., ["server.host", "server.port"])
        """
        keys = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                keys.append(full_key)
                
                # Recurse into nested dictionaries
                if max_depth > 0 and isinstance(value, dict):
                    nested_keys = self._extract_keys(value, full_key, max_depth - 1)
                    keys.extend(nested_keys)
                
                # Note list values
                elif isinstance(value, list) and len(value) > 0:
                    keys.append(f"{full_key}[{len(value)} items]")
        
        elif isinstance(data, list):
            if len(data) > 0:
                keys.append(f"List[{len(data)} items]")
                
                # If list contains dicts, show structure
                if isinstance(data[0], dict):
                    sample_keys = list(data[0].keys())[:5]  # First 5 keys
                    keys.append(f"  └─ Sample keys: {', '.join(sample_keys)}")
        
        else:
            # Primitive value
            keys.append(f"Primitive: {type(data).__name__}")
        
        return keys