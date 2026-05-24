"""Unit tests for the prompts module."""

from claudecode.prompts import get_security_audit_prompt


class TestPrompts:
    """Test prompt generation functions."""
    
    def test_get_security_audit_prompt_basic(self):
        """Test basic security audit prompt generation."""
        pr_data = {
            "number": 123,
            "title": "Add new feature",
            "body": "This PR adds a new feature to handle user input",
            "user": "testuser",
            "changed_files": 1,
            "additions": 10,
            "deletions": 5,
            "head": {
                "repo": {
                    "full_name": "owner/repo"
                }
            },
            "files": [
                {
                    "filename": "app.py",
                    "status": "modified",
                    "additions": 10,
                    "deletions": 5
                }
            ]
        }
        
        pr_diff = """
diff --git a/app.py b/app.py
@@ -1,5 +1,10 @@
 def process_input(user_input):
-    return user_input
+    # Process the input
+    result = eval(user_input)  # Potential security issue
+    return result
"""
        
        prompt = get_security_audit_prompt(pr_data, pr_diff)
        
        # Check that prompt contains expected elements
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "123" in prompt  # PR number
        assert "Add new feature" in prompt  # PR title
        assert "testuser" in prompt  # Author
        assert "app.py" in prompt  # File name
        assert "eval(user_input)" in prompt  # The actual diff content
    
    def test_get_security_audit_prompt_empty_body(self):
        """Test prompt generation with empty PR body."""
        pr_data = {
            "number": 456,
            "title": "Quick fix",
            "body": None,  # Empty body
            "user": "author",
            "changed_files": 0,
            "additions": 0,
            "deletions": 0,
            "head": {
                "repo": {
                    "full_name": "owner/repo"
                }
            },
            "files": []
        }
        
        pr_diff = "diff --git a/test.js b/test.js"
        
        prompt = get_security_audit_prompt(pr_data, pr_diff)
        
        assert isinstance(prompt, str)
        assert "456" in prompt
        assert "Quick fix" in prompt
        assert "author" in prompt
    
    def test_get_security_audit_prompt_multiple_files(self):
        """Test prompt generation with multiple files."""
        pr_data = {
            "number": 789,
            "title": "Security improvements",
            "body": "Fixing various security issues",
            "user": "security-team",
            "changed_files": 3,
            "additions": 70,
            "deletions": 110,
            "head": {
                "repo": {
                    "full_name": "owner/repo"
                }
            },
            "files": [
                {
                    "filename": "auth.py",
                    "status": "modified",
                    "additions": 20,
                    "deletions": 10
                },
                {
                    "filename": "config.yaml",
                    "status": "added",
                    "additions": 50,
                    "deletions": 0
                },
                {
                    "filename": "old_auth.py",
                    "status": "deleted",
                    "additions": 0,
                    "deletions": 100
                }
            ]
        }
        
        pr_diff = """
diff --git a/auth.py b/auth.py
@@ -1,10 +1,20 @@
+import secrets
+
diff --git a/config.yaml b/config.yaml
@@ -0,0 +1,50 @@
+database:
+  password: "hardcoded_password"
"""
        
        prompt = get_security_audit_prompt(pr_data, pr_diff)
        
        # Check all files are mentioned
        assert "auth.py" in prompt
        assert "config.yaml" in prompt
        assert "old_auth.py" in prompt
        
        # Check file statuses
        assert "modified" in prompt.lower()
        assert "added" in prompt.lower()
        assert "deleted" in prompt.lower()
    
    def test_get_security_audit_prompt_special_characters(self):
        """Test prompt generation with special characters."""
        pr_data = {
            "number": 999,
            "title": "Fix SQL injection in user's profile",
            "body": "This fixes a SQL injection vulnerability in the `get_user()` function",
            "user": "user-with-dash",
            "changed_files": 1,
            "additions": 5,
            "deletions": 3,
            "head": {
                "repo": {
                    "full_name": "owner/repo"
                }
            },
            "files": [
                {
                    "filename": "src/db/queries.py",
                    "status": "modified",
                    "additions": 5,
                    "deletions": 3
                }
            ]
        }
        
        pr_diff = """
diff --git a/src/db/queries.py b/src/db/queries.py
@@ -10,3 +10,5 @@
-    query = f"SELECT * FROM users WHERE id = {user_id}"
+    query = "SELECT * FROM users WHERE id = ?"
+    cursor.execute(query, (user_id,))
"""
        
        prompt = get_security_audit_prompt(pr_data, pr_diff)
        
        # Check special characters are preserved
        assert "user's" in prompt
        assert "user-with-dash" in prompt
        assert "src/db/queries.py" in prompt
    
    def test_get_security_audit_prompt_no_files(self):
        """Test prompt generation with no files (edge case)."""
        pr_data = {
            "number": 111,
            "title": "Documentation update",
            "body": "Just updating docs",
            "user": "doc-author",
            "changed_files": 0,
            "additions": 0,
            "deletions": 0,
            "head": {
                "repo": {
                    "full_name": "owner/repo"
                }
            },
            "files": []  # No files
        }
        
        pr_diff = ""  # Empty diff
        
        prompt = get_security_audit_prompt(pr_data, pr_diff)
        
        assert isinstance(prompt, str)
        assert "111" in prompt
        assert "Documentation update" in prompt
    
    def test_get_security_audit_prompt_structure(self):
        """Test that prompt has expected structure."""
        pr_data = {
            "number": 42,
            "title": "Test PR",
            "body": "Test description",
            "user": "testuser",
            "changed_files": 1,
            "additions": 1,
            "deletions": 1,
            "head": {
                "repo": {
                    "full_name": "owner/repo"
                }
            },
            "files": [
                {
                    "filename": "test.py",
                    "status": "modified",
                    "additions": 1,
                    "deletions": 1
                }
            ]
        }
        
        pr_diff = "diff --git a/test.py b/test.py\n+print('test')"
        
        prompt = get_security_audit_prompt(pr_data, pr_diff)
        
        # Should contain sections for metadata and diff
        assert "PR #" in prompt or "Pull Request" in prompt
        assert "Title:" in prompt or pr_data["title"] in prompt
        assert "Author:" in prompt or pr_data["user"]["login"] in prompt
        assert "Files:" in prompt or "test.py" in prompt
        
        # Should contain the actual diff
        assert pr_diff in prompt or "print('test')" in prompt
    
    def test_get_security_audit_prompt_long_diff(self):
        """Test prompt generation with very long diff."""
        pr_data = {
            "number": 12345,
            "title": "Major refactoring",
            "body": "Refactoring the entire codebase",
            "user": "refactor-bot",
            "changed_files": 10,
            "additions": 1000,
            "deletions": 500,
            "head": {
                "repo": {
                    "full_name": "owner/repo"
                }
            },
            "files": [
                {
                    "filename": f"file{i}.py",
                    "status": "modified",
                    "additions": 100,
                    "deletions": 50
                }
                for i in range(10)
            ]
        }
        
        # Create a large diff
        pr_diff = "\n".join([
            f"diff --git a/file{i}.py b/file{i}.py\n" +
            "\n".join([f"+line {j}" for j in range(50)])
            for i in range(10)
        ])
        
        prompt = get_security_audit_prompt(pr_data, pr_diff)
        
        # Should handle large diffs without error
        assert isinstance(prompt, str)
        assert len(prompt) > 1000  # Should be substantial
        assert "12345" in prompt
        assert "Major refactoring" in prompt
    
    def test_get_security_audit_prompt_unicode(self):
        """Test prompt generation with unicode characters."""
        pr_data = {
            "number": 666,
            "title": "Add emoji support 🎉",
            "body": "This PR adds emoji rendering 🔒 🛡️",
            "user": "émoji-user",
            "changed_files": 1,
            "additions": 42,
            "deletions": 0,
            "head": {
                "repo": {
                    "full_name": "owner/repo"
                }
            },
            "files": [
                {
                    "filename": "émojis.py",
                    "status": "added",
                    "additions": 42,
                    "deletions": 0
                }
            ]
        }
        
        pr_diff = """
diff --git a/émojis.py b/émojis.py
+# 🔒 Security check
+def check_input(text: str) -> bool:
+    return "🚨" not in text
"""
        
        prompt = get_security_audit_prompt(pr_data, pr_diff)
        
        # Check unicode is preserved
        assert "🎉" in prompt  # Title emoji
        assert "émoji-user" in prompt
        assert "émojis.py" in prompt
        assert "🚨" in prompt  # From diff