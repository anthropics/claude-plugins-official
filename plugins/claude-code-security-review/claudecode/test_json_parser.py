"""Unit tests for the json_parser module."""

import json
from typing import Any, Dict
from claudecode.json_parser import parse_json_with_fallbacks, extract_json_from_text


class TestJsonParser:
    """Test JSON parsing utilities."""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON string."""
        valid_json = '{"key": "value", "number": 42, "array": [1, 2, 3]}'
        success, result = parse_json_with_fallbacks(valid_json)
        
        assert success is True
        assert result == {"key": "value", "number": 42, "array": [1, 2, 3]}
    
    def test_parse_json_with_whitespace(self):
        """Test parsing JSON with extra whitespace."""
        json_with_spaces = '  \n  {"key": "value"}  \n  '
        success, result = parse_json_with_fallbacks(json_with_spaces)
        
        assert success is True
        assert result == {"key": "value"}
    
    def test_parse_empty_json_object(self):
        """Test parsing empty JSON object."""
        success, result = parse_json_with_fallbacks('{}')
        assert success is True
        assert result == {}
    
    def test_parse_empty_json_array(self):
        """Test parsing empty JSON array."""
        success, result = parse_json_with_fallbacks('[]')
        assert success is True
        assert result == []
    
    def test_parse_nested_json(self):
        """Test parsing nested JSON structures."""
        nested_json = '''
        {
            "level1": {
                "level2": {
                    "level3": ["a", "b", "c"]
                }
            }
        }
        '''
        success, result = parse_json_with_fallbacks(nested_json)
        
        assert success is True
        assert isinstance(result, dict)
        # Type narrowing for pyright
        result_dict: Dict[str, Any] = result
        assert result_dict["level1"]["level2"]["level3"] == ["a", "b", "c"]
    
    def test_parse_json_with_unicode(self):
        """Test parsing JSON with unicode characters."""
        unicode_json = '{"emoji": "🔒", "text": "Hello λ world"}'
        success, result = parse_json_with_fallbacks(unicode_json)
        
        assert success is True
        assert result["emoji"] == "🔒"
        assert result["text"] == "Hello λ world"
    
    def test_parse_json_with_escaped_characters(self):
        """Test parsing JSON with escaped characters."""
        escaped_json = '{"path": "C:\\\\Users\\\\test", "quote": "\\"Hello\\""}'
        success, result = parse_json_with_fallbacks(escaped_json)
        
        assert success is True
        assert result["path"] == "C:\\Users\\test"
        assert result["quote"] == '"Hello"'
    
    def test_extract_json_from_text_with_backticks(self):
        """Test extracting JSON from markdown code blocks."""
        text_with_json = '''
        Here is some text before the JSON:
        
        ```json
        {"extracted": true, "value": 123}
        ```
        
        And some text after.
        '''
        result = extract_json_from_text(text_with_json)
        
        assert result == {"extracted": True, "value": 123}
    
    def test_extract_json_from_text_without_backticks(self):
        """Test extracting JSON from plain text."""
        text_with_json = '''
        Some text before
        {"plain": "json", "number": 456}
        Some text after
        '''
        result = extract_json_from_text(text_with_json)
        
        assert result == {"plain": "json", "number": 456}
    
    def test_extract_json_array_from_text(self):
        """Test extracting JSON array from text (currently not supported)."""
        text_with_array = '''
        Results:
        [{"id": 1}, {"id": 2}, {"id": 3}]
        Done.
        '''
        result = extract_json_from_text(text_with_array)
        
        # The function currently only extracts objects, not arrays
        # It should extract the first object it finds
        assert result == {"id": 1}
    
    def test_extract_json_with_multiple_blocks(self):
        """Test extracting JSON when multiple JSON blocks exist."""
        text_with_multiple = '''
        First block:
        {"first": true}
        
        Second block:
        {"second": true, "larger": "block"}
        '''
        # Should extract the first valid JSON block found
        result = extract_json_from_text(text_with_multiple)
        
        assert result == {"first": True} or result == {"second": True, "larger": "block"}
    
    def test_parse_invalid_json_returns_error(self):
        """Test parsing invalid JSON returns error."""
        invalid_jsons = [
            '{invalid json}',
            '{"unclosed": "string}',
            '{"trailing": "comma",}',
            '{unquoted: key}',
            'not json at all',
            ''
        ]
        
        for invalid in invalid_jsons:
            success, result = parse_json_with_fallbacks(invalid)
            assert success is False
            assert "error" in result
    
    def test_extract_json_from_text_no_json(self):
        """Test extracting JSON from text with no JSON returns None."""
        texts_without_json = [
            'This is just plain text',
            '```python\nprint("hello")\n```',
            '',
            None
        ]
        
        for text in texts_without_json:
            result = extract_json_from_text(text)
            assert result is None
    
    def test_parse_json_with_comments(self):
        """Test parsing JSON that might have comments (should fail)."""
        json_with_comments = '''
        {
            // This is a comment
            "key": "value"
        }
        '''
        success, result = parse_json_with_fallbacks(json_with_comments)
        assert success is False  # Standard JSON doesn't support comments
        assert "error" in result
    
    def test_extract_json_with_syntax_errors_in_text(self):
        """Test extracting JSON when there are syntax errors in surrounding text."""
        text = '''
        Here's some code with errors: print(
        
        But the JSON is valid:
        {"valid": "json", "number": 789}
        
        More broken code: }{][
        '''
        result = extract_json_from_text(text)
        
        assert result == {"valid": "json", "number": 789}
    
    def test_large_json_parsing(self):
        """Test parsing large JSON structures."""
        large_json = {
            "findings": [
                {
                    "id": i,
                    "title": f"Finding {i}",
                    "description": f"Description for finding {i}",
                    "severity": "medium",
                    "file": f"/path/to/file{i}.py",
                    "line": i * 10
                }
                for i in range(100)
            ]
        }
        
        json_string = json.dumps(large_json)
        success, result = parse_json_with_fallbacks(json_string)
        
        assert success is True
        assert result == large_json
        assert len(result["findings"]) == 100
    
    def test_json_with_special_characters_in_strings(self):
        """Test JSON with special characters in string values."""
        special_json = {
            "newline": "line1\nline2",
            "tab": "before\tafter",
            "backslash": "path\\to\\file",
            "quotes": 'He said "Hello"',
            "unicode": "café ☕",
            "emoji": "🔒 Security 🛡️"
        }
        
        json_string = json.dumps(special_json)
        success, result = parse_json_with_fallbacks(json_string)
        
        assert success is True
        assert result == special_json
    
    def test_extract_json_from_nested_code_blocks(self):
        """Test extracting JSON from nested code blocks."""
        text = '''
        Here's a code block within text:
        
        ```
        Some other code
        ```json
        {"nested": "json"}
        ```
        ```
        '''
        result = extract_json_from_text(text)
        
        # Should be able to extract the JSON
        assert result == {"nested": "json"}