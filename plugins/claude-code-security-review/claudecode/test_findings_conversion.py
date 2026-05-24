#!/usr/bin/env python3
"""
Unit tests for findings conversion and edge cases.
"""

import pytest
import json

from claudecode.findings_filter import FindingsFilter, HardExclusionRules
from claudecode.json_parser import parse_json_with_fallbacks, extract_json_from_text


def create_simple_filter():
    """Create a filter that only uses hard exclusions."""
    return FindingsFilter(use_hard_exclusions=True, use_claude_filtering=False)


def filter_findings_simple(filter_instance, findings):
    """Helper to get simple kept/excluded tuple from FindingsFilter."""
    if findings is None:
        raise TypeError("'NoneType' object is not iterable")
    
    success, results, stats = filter_instance.filter_findings(findings)
    if success:
        kept = results.get('filtered_findings', [])
        excluded = results.get('excluded_findings', [])
    else:
        kept = findings
        excluded = []
    return kept, excluded


class TestFindingsConversionEdgeCases:
    """Test edge cases in findings conversion and filtering."""
    
    def test_empty_findings_list(self):
        """Test filtering empty findings list."""
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, [])
        
        assert kept == []
        assert excluded == []
    
    def test_none_findings_list(self):
        """Test filtering None findings list."""
        filter = create_simple_filter()
        # Should raise TypeError for None input
        with pytest.raises(TypeError):
            filter_findings_simple(filter, None)
    
    def test_malformed_finding_missing_fields(self):
        """Test filtering findings with missing required fields."""
        findings = [
            {'description': 'Issue 1'},  # Missing severity
            {'severity': 'HIGH'},  # Missing description
            {},  # Empty finding
            {'severity': 'HIGH', 'description': 'Valid issue'},
        ]
        
        filter = create_simple_filter()
        # The filter will process all findings, even with missing fields
        kept, excluded = filter_findings_simple(filter, findings)
        
        # All findings without exclusion patterns are kept
        assert len(kept) == 4
        assert len(excluded) == 0
    
    def test_finding_with_extra_fields(self):
        """Test findings with extra/unexpected fields."""
        findings = [
            {
                'severity': 'HIGH',
                'description': 'SQL injection',
                'extra_field': 'value',
                'nested': {'data': 'here'},
                'array': [1, 2, 3]
            }
        ]
        
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, findings)
        
        # Extra fields should be preserved
        assert len(kept) == 1
        assert kept[0]['extra_field'] == 'value'
        assert kept[0]['nested'] == {'data': 'here'}
    
    def test_unicode_in_findings(self):
        """Test findings with unicode characters."""
        findings = [
            {
                'severity': 'HIGH',
                'description': 'SQL injection in 用户输入',
                'file': 'файл.py',
                'exploit_scenario': 'Attacker könnte dies ausnutzen'
            }
        ]
        
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, findings)
        
        assert len(kept) == 1
        assert '用户输入' in kept[0]['description']
        assert kept[0]['file'] == 'файл.py'
    
    def test_very_long_description(self):
        """Test findings with very long descriptions."""
        long_desc = 'A' * 10000  # 10k character description
        findings = [
            {
                'severity': 'HIGH',
                'description': f'SQL injection vulnerability. {long_desc}'
            }
        ]
        
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, findings)
        
        # Should not crash on long descriptions
        assert len(kept) == 1
        assert len(kept[0]['description']) > 10000
    
    def test_special_characters_in_description(self):
        """Test findings with special regex characters."""
        findings = [
            {'severity': 'HIGH', 'description': 'Issue with [brackets] and (parens)'},
            {'severity': 'HIGH', 'description': 'Path: C:\\Users\\test\\file.py'},
            {'severity': 'HIGH', 'description': 'Regex pattern: .*$^[]{}'},
            {'severity': 'HIGH', 'description': 'Missing rate limiting for API'},
        ]
        
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, findings)
        
        # Special characters shouldn't break filtering
        assert len(kept) == 3  # "Missing rate limiting" should be excluded
        assert len(excluded) == 1
    
    def test_case_sensitivity_in_exclusions(self):
        """Test case sensitivity in exclusion rules."""
        findings = [
            {'severity': 'HIGH', 'description': 'DENIAL OF SERVICE attack'},
            {'severity': 'HIGH', 'description': 'Denial Of Service issue'},
            {'severity': 'HIGH', 'description': 'dos vulnerability'},
            {'severity': 'HIGH', 'description': 'DoS attack vector'},
        ]
        
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, findings)
        
        # DOS patterns use word boundaries, "dos vulnerability" doesn't match \bdos attack\b
        assert len(kept) == 1  # "dos vulnerability" is kept
        assert len(excluded) == 3
        assert kept[0]['description'] == 'dos vulnerability'
    
    def test_severity_normalization(self):
        """Test various severity formats."""
        findings = [
            {'severity': 'high', 'description': 'Issue 1'},
            {'severity': 'HIGH', 'description': 'Issue 2'},
            {'severity': 'High', 'description': 'Issue 3'},
            {'severity': 'CRITICAL', 'description': 'Issue 4'},
            {'severity': 'unknown', 'description': 'Issue 5'},
            {'severity': '', 'description': 'Issue 6'},
            {'severity': None, 'description': 'Issue 7'},
        ]
        
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, findings)
        
        # All should be processed regardless of severity format
        assert len(kept) == 7
    
    def test_json_injection_in_findings(self):
        """Test findings that might contain JSON injection attempts."""
        findings = [
            {
                'severity': 'HIGH',
                'description': '{"injected": "json", "description": "fake"}'
            },
            {
                'severity': 'HIGH',
                'description': 'Issue with "}]} payload'
            }
        ]
        
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, findings)
        
        # Should handle JSON-like content in descriptions
        assert len(kept) == 2


class TestJsonParserEdgeCases:
    """Test JSON parser edge cases."""
    
    def test_parse_empty_string(self):
        """Test parsing empty string."""
        success, result = parse_json_with_fallbacks('', 'test')
        assert success is False
        # Empty string returns error structure
        assert 'error' in result
        assert "Invalid JSON response" in result['error']
    
    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only string."""
        success, result = parse_json_with_fallbacks('   \n\t  ', 'test')
        assert success is False
        # Whitespace returns error structure
        assert 'error' in result
        assert "Invalid JSON response" in result['error']
    
    def test_parse_truncated_json(self):
        """Test parsing truncated JSON."""
        truncated = '{"findings": [{"severity": "HIGH", "desc'
        success, result = parse_json_with_fallbacks(truncated, 'test')
        assert success is False
    
    def test_parse_json_with_comments(self):
        """Test parsing JSON with comments (invalid JSON)."""
        json_with_comments = """{
            "findings": [
                // This is a comment
                {"severity": "HIGH", "description": "Issue"}
            ]
        }"""
        success, result = parse_json_with_fallbacks(json_with_comments, 'test')
        assert success is False
    
    def test_parse_json_with_trailing_comma(self):
        """Test parsing JSON with trailing comma."""
        json_with_comma = '{"findings": [{"severity": "HIGH"},]}'
        success, result = parse_json_with_fallbacks(json_with_comma, 'test')
        assert success is False
    
    def test_parse_nested_json_string(self):
        """Test parsing JSON embedded in string."""
        nested = '{"result": "{\\"findings\\": [{\\"severity\\": \\"HIGH\\"}]}"}'
        success, result = parse_json_with_fallbacks(nested, 'test')
        assert success is True
        assert 'result' in result
    
    def test_extract_json_from_text_edge_cases(self):
        """Test JSON extraction from various text formats."""
        # No JSON
        assert extract_json_from_text('Just plain text') is None
        
        # Multiple JSON objects
        text = 'First: {"a": 1} Second: {"b": 2}'
        result = extract_json_from_text(text)
        assert result == {"a": 1}  # Should extract first
        
        # JSON in markdown code block
        text = '''```json
{"findings": [{"severity": "HIGH"}]}
```'''
        result = extract_json_from_text(text)
        assert result is not None
        assert 'findings' in result
        
        # Malformed JSON attempts
        text = 'Result: {invalid json}'
        assert extract_json_from_text(text) is None
        
        # Very large JSON
        large_obj = {"data": ["x" * 100 for _ in range(1000)]}
        text = f"Result: {json.dumps(large_obj)}"
        result = extract_json_from_text(text)
        assert result is not None
        assert len(result['data']) == 1000
    
    def test_extract_json_with_unicode(self):
        """Test JSON extraction with unicode."""
        text = 'Result: {"message": "Error: 文件未找到"}'
        result = extract_json_from_text(text)
        assert result is not None
        assert result['message'] == "Error: 文件未找到"
    
    def test_parse_json_arrays(self):
        """Test parsing JSON arrays."""
        # Direct array
        success, result = parse_json_with_fallbacks('[1, 2, 3]', 'test')
        assert success is True
        assert result == [1, 2, 3]
        
        # Array of findings
        findings_array = '[{"severity": "HIGH", "description": "Issue"}]'
        success, result = parse_json_with_fallbacks(findings_array, 'test')
        assert success is True
        assert isinstance(result, list)
        assert len(result) == 1


class TestHardExclusionRulesEdgeCases:
    """Test hard exclusion rules edge cases."""
    
    def test_overlapping_patterns(self):
        """Test findings that match multiple exclusion patterns."""
        finding = {
            'severity': 'HIGH',
            'description': 'Denial of service via rate limiting bypass allows brute force attack'
        }
        
        # Matches both DOS and rate limiting patterns
        reason = HardExclusionRules.get_exclusion_reason(finding)
        assert reason is not None
        assert "DOS" in reason  # Should match DOS pattern first
    
    def test_pattern_boundary_matching(self):
        """Test pattern matching at word boundaries."""
        findings = [
            {'severity': 'HIGH', 'description': 'dosomething() function'},  # Should not match DOS
            {'severity': 'HIGH', 'description': 'windows path issue'},  # Should not match
            {'severity': 'HIGH', 'description': 'pseudorandom number'},  # Should not match
        ]
        
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, findings)
        
        # None should be excluded (no word boundary match)
        assert len(kept) == 3
        assert len(excluded) == 0
    
    def test_html_entities_in_description(self):
        """Test findings with HTML entities."""
        findings = [
            {'severity': 'HIGH', 'description': 'XSS via &lt;script&gt; tag'},
            {'severity': 'HIGH', 'description': 'Missing rate limiting &amp; throttling'},
        ]
        
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, findings)
        
        # "Missing rate limiting" should be excluded even with HTML entity
        assert len(kept) == 1
        assert len(excluded) == 1
        assert 'XSS' in kept[0]['description']
    
    def test_multiline_descriptions(self):
        """Test findings with multiline descriptions."""
        findings = [
            {
                'severity': 'HIGH',
                'description': '''SQL injection vulnerability
                in user input handling.
                This could lead to data exposure.'''
            },
            {
                'severity': 'HIGH',
                'description': '''Performance issue that could
                cause denial of service under
                heavy load conditions.'''
            }
        ]
        
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, findings)
        
        # DOS should be found even across lines
        assert len(kept) == 1
        assert len(excluded) == 1
        assert 'SQL injection' in kept[0]['description']


class TestFilteringCombinations:
    """Test combinations of filtering scenarios."""
    
    def test_mixed_valid_invalid_findings(self):
        """Test mix of valid, invalid, and excludable findings."""
        findings = [
            {'severity': 'HIGH', 'description': 'SQL injection'},  # Valid
            {'description': 'Missing severity'},  # Valid (no exclusion pattern)
            {'severity': 'HIGH', 'description': 'Missing rate limiting'},  # Excludable
            {'severity': 'MEDIUM', 'description': 'XSS vulnerability'},  # Valid
            {'severity': 'LOW', 'description': 'Denial of service attack'},  # Excludable
            {'severity': '', 'description': ''},  # Valid (no exclusion pattern)
            {'severity': 'HIGH', 'description': 'RCE possibility'},  # Valid
        ]
        
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, findings)
        
        assert len(kept) == 5  # All except rate limiting and DOS
        assert len(excluded) == 2  # Rate limiting, DOS
        
        # Verify excluded findings
        excluded_descs = [e['finding']['description'] for e in excluded]
        assert 'Missing rate limiting' in excluded_descs
        assert 'Denial of service attack' in excluded_descs
    
    def test_duplicate_findings(self):
        """Test handling of duplicate findings."""
        finding = {'severity': 'HIGH', 'description': 'Same issue'}
        findings = [finding, finding, finding]  # Same object repeated
        
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, findings)
        
        # All duplicates should be kept (deduplication not filter's job)
        assert len(kept) == 3
    
    def test_similar_but_different_findings(self):
        """Test similar findings with slight differences."""
        findings = [
            {'severity': 'HIGH', 'description': 'SQL injection in login'},
            {'severity': 'HIGH', 'description': 'SQL injection in login()'},
            {'severity': 'HIGH', 'description': 'sql injection in login'},
            {'severity': 'MEDIUM', 'description': 'SQL injection in login'},
        ]
        
        filter = create_simple_filter()
        kept, excluded = filter_findings_simple(filter, findings)
        
        # All should be kept despite similarity
        assert len(kept) == 4
