#!/usr/bin/env bun

/**
 * Unit tests for comment-pr-findings.js using Bun test runner
 */

import { test, expect, describe, beforeEach, afterEach, mock, spyOn } from "bun:test";

describe('comment-pr-findings.js', () => {
  let originalEnv;
  let consoleLogSpy;
  let consoleErrorSpy;
  let processExitSpy;
  let readFileSyncSpy;
  let spawnSyncSpy;

  // Helper function to create mock responses for spawnSync
  function mockSpawnSyncResponse(endpoint, method = 'GET', captureData = null) {
    return (cmd, args, options) => {
      if (cmd === 'gh' && args.includes('api')) {
        const apiEndpoint = args[1];
        const apiMethod = args[args.indexOf('--method') + 1] || 'GET';
        
        if (apiEndpoint.includes(endpoint) && apiMethod === method) {
          if (captureData && options && options.input) {
            captureData.data = JSON.parse(options.input);
          }
          return { status: 0, stdout: captureData?.response || '{}', stderr: '' };
        }
      }
      return null;
    };
  }

  beforeEach(() => {
    // Save original environment
    originalEnv = { ...process.env };
    
    // Clear process.env completely first
    for (const key in process.env) {
      delete process.env[key];
    }
    setupTestEnvironment();
    
    // Set up spies
    consoleLogSpy = spyOn(console, 'log').mockImplementation(() => {});
    consoleErrorSpy = spyOn(console, 'error').mockImplementation(() => {});
    processExitSpy = spyOn(process, 'exit').mockImplementation(() => {});
    
    // Mock fs and child_process
    readFileSyncSpy = spyOn(require('fs'), 'readFileSync');
    spawnSyncSpy = spyOn(require('child_process'), 'spawnSync');
  });

  afterEach(() => {
    // Restore environment
    process.env = originalEnv;
    
    // Clear module cache to allow re-running the script
    delete require.cache[require.resolve('./comment-pr-findings.js')];
  });

  // Set up common test environment
  function setupTestEnvironment() {
    process.env.GITHUB_REPOSITORY = 'owner/repo';
    process.env.GITHUB_EVENT_PATH = 'github-event.json';
  }

  describe('Environment Setup', () => {
    test('should parse GitHub context correctly', async () => {

      const mockEventData = {
        pull_request: {
          number: 123,
          head: { sha: 'abc123' }
        }
      };
      
      readFileSyncSpy.mockImplementation((path) => {
        if (path.includes('github-event.json')) {
          return JSON.stringify(mockEventData);
        }
        if (path === 'findings.json') {
          return '[]'; // Empty findings to exit early
        }
      });

      await import('./comment-pr-findings.js');
      
      expect(readFileSyncSpy).toHaveBeenCalledWith(expect.stringContaining('github-event.json'), 'utf8');
    });
  });

  describe('Finding Processing', () => {
    test('should exit early when no findings file exists', async () => {
      readFileSyncSpy.mockImplementation((path) => {
        if (path.includes('github-event.json')) {
          return JSON.stringify({
            pull_request: {
              number: 123,
              head: { sha: 'abc123' }
            }
          });
        }
        if (path === 'findings.json') {
          throw new Error('File not found');
        }
        // For any other file (like the script itself), throw to prevent loading
        throw new Error('Unexpected file read: ' + path);
      });

      await import('./comment-pr-findings.js');
      
      expect(consoleLogSpy).toHaveBeenCalledWith('Could not read findings file');
      expect(spawnSyncSpy).not.toHaveBeenCalled();
    });

    test('should exit early when findings array is empty', async () => {
      readFileSyncSpy.mockReturnValue('[]');

      await import('./comment-pr-findings.js');
      
      expect(spawnSyncSpy).not.toHaveBeenCalled();
    });

    test('should process findings correctly', async () => {
      const mockFindings = [{
        path: 'test.py',
        start: { line: 10 },
        check_id: 'rules.insecure-pickle-loads-autofix',
        extra: {
          message: 'Detected use of pickle deserialization',
          fix: 'json.loads($DATA)  # Use json.loads() instead of pickle for security'
        }
      }];

      const mockPrFiles = [{
        filename: 'test.py',
        patch: '@@ -10,1 +10,1 @@'
      }];

      const mockFileContent = {
        content: Buffer.from('    data = pickle.loads(user_input)').toString('base64')
      };

      readFileSyncSpy.mockImplementation((path) => {
        if (path.includes('github-event.json')) {
          return JSON.stringify({
            pull_request: {
              number: 123,
              head: { sha: 'abc123' }
            }
          });
        }
        if (path === 'findings.json') {
          return JSON.stringify(mockFindings);
        }
      });

      let reviewDataCaptured = null;
      spawnSyncSpy.mockImplementation((cmd, args, options) => {
        if (cmd === 'gh' && args.includes('api')) {
          const endpoint = args[1];
          if (endpoint.includes('/pulls/123/files')) {
            return { status: 0, stdout: JSON.stringify(mockPrFiles), stderr: '' };
          }
          if (endpoint.includes('/contents/test.py')) {
            return { status: 0, stdout: JSON.stringify(mockFileContent), stderr: '' };
          }
          if (endpoint.includes('/pulls/123/comments') && args.includes('GET')) {
            return { status: 0, stdout: '[]', stderr: '' }; // No existing comments
          }
          if (endpoint.includes('/pulls/123/reviews') && args.includes('POST')) {
            // Capture the review data if passed
            if (options && options.input) {
              reviewDataCaptured = JSON.parse(options.input);
            }
            return { status: 0, stdout: '{}', stderr: '' };
          }
          return { status: 0, stdout: '{}', stderr: '' };
        }
        return { status: 0, stdout: '{}', stderr: '' };
      });

      await import('./comment-pr-findings.js');

      // Verify API calls were made
      expect(spawnSyncSpy).toHaveBeenCalledWith('gh', expect.arrayContaining(['api', expect.stringContaining('/pulls/123/files')]), expect.any(Object));
      expect(spawnSyncSpy).toHaveBeenCalledWith('gh', expect.arrayContaining(['api', expect.stringContaining('/pulls/123/reviews')]), expect.any(Object));
      expect(consoleLogSpy).toHaveBeenCalledWith('Created review with 1 inline comments');
      
      // Verify review data was captured
      expect(reviewDataCaptured).toBeTruthy();
      expect(reviewDataCaptured.comments).toHaveLength(1);
    });
  });

  describe('Autofix Suggestions', () => {
    test('should generate correct pickle.loads autofix', async () => {
     
      const mockFindings = [{
        path: 'test.py',
        start: { line: 1 },
        check_id: 'rules.insecure-pickle-loads-autofix',
        extra: {
          message: 'Insecure pickle loads',
          fix: 'json.loads($DATA)  # Use json.loads() instead of pickle for security'
        }
      }];

      readFileSyncSpy.mockImplementation((path) => {
        if (path.includes('github-event.json')) {
          return JSON.stringify({
            pull_request: { number: 123, head: { sha: 'abc123' } }
          });
        }
        if (path === 'findings.json') {
          return JSON.stringify(mockFindings);
        }
      });

      let capturedReviewData;
      spawnSyncSpy.mockImplementation((cmd, args, options) => {
        if (cmd === 'gh' && args.includes('api')) {
          const endpoint = args[1];
          const method = args[args.indexOf('--method') + 1] || 'GET';
          
          if (endpoint.includes('/pulls/123/files')) {
            return { status: 0, stdout: JSON.stringify([{ filename: 'test.py' }]), stderr: '' };
          }
          if (endpoint.includes('/contents/test.py')) {
            return { status: 0, stdout: JSON.stringify({
              content: Buffer.from('result = pickle.loads(data)').toString('base64')
            }), stderr: '' };
          }
          if (endpoint.includes('/pulls/123/comments') && method === 'GET') {
            return { status: 0, stdout: '[]', stderr: '' };
          }
          if (endpoint.includes('/pulls/123/reviews') && method === 'POST') {
            if (options && options.input) {
              capturedReviewData = JSON.parse(options.input);
            }
            return { status: 0, stdout: '{}', stderr: '' };
          }
          return { status: 0, stdout: '{}', stderr: '' };
        }
        return { status: 0, stdout: '{}', stderr: '' };
      });

      await import('./comment-pr-findings.js')
      expect(capturedReviewData).toBeDefined();
      expect(capturedReviewData.comments[0].body).toContain('🤖 **Security Issue: Insecure pickle loads**');
    });

    test('should generate correct yaml.load autofix', async () => {
     
      const mockFindings = [{
        path: 'config.py',
        start: { line: 1 },
        check_id: 'rules.insecure-yaml-loads-no-loader',
        extra: {
          message: 'Unsafe YAML deserialization',
          fix: 'yaml.safe_load($DATA)'
        }
      }];

      readFileSyncSpy.mockImplementation((path) => {
        if (path.includes('github-event.json')) {
          return JSON.stringify({
            pull_request: { number: 123, head: { sha: 'abc123' } }
          });
        }
        if (path === 'findings.json') {
          return JSON.stringify(mockFindings);
        }
      });

      let capturedReviewData;
      spawnSyncSpy.mockImplementation((cmd, args, options) => {
        if (cmd === 'gh' && args.includes('api')) {
          const endpoint = args[1];
          const method = args[args.indexOf('--method') + 1] || 'GET';
          
          if (endpoint.includes('/pulls/123/files')) {
            return { status: 0, stdout: JSON.stringify([{ filename: 'config.py' }]), stderr: '' };
          }
          if (endpoint.includes('/contents/config.py')) {
            return { status: 0, stdout: JSON.stringify({
              content: Buffer.from('config = yaml.load(config_file)').toString('base64')
            }), stderr: '' };
          }
          if (endpoint.includes('/pulls/123/comments') && method === 'GET') {
            return { status: 0, stdout: '[]', stderr: '' };
          }
          if (endpoint.includes('/pulls/123/reviews') && method === 'POST') {
            if (options && options.input) {
              capturedReviewData = JSON.parse(options.input);
            }
            return { status: 0, stdout: '{}', stderr: '' };
          }
          return { status: 0, stdout: '{}', stderr: '' };
        }
        return { status: 0, stdout: '{}', stderr: '' };
      });

      await import('./comment-pr-findings.js')
      expect(capturedReviewData).toBeDefined();
      expect(capturedReviewData.comments[0].body).toContain('🤖 **Security Issue: Unsafe YAML deserialization**');
    });

    test('should preserve indentation in autofix', async () => {
     
      const mockFindings = [{
        path: 'test.py',
        start: { line: 1 },
        check_id: 'rules.insecure-pickle-loads-autofix',
        extra: {
          message: 'Insecure pickle loads',
          fix: 'json.loads($DATA)  # Use json.loads() instead of pickle for security'
        }
      }];

      readFileSyncSpy.mockImplementation((path) => {
        if (path.includes('github-event.json')) {
          return JSON.stringify({
            pull_request: { number: 123, head: { sha: 'abc123' } }
          });
        }
        if (path === 'findings.json') {
          return JSON.stringify(mockFindings);
        }
      });

      let capturedReviewData;
      spawnSyncSpy.mockImplementation((cmd, args, options) => {
        if (cmd === 'gh' && args.includes('api')) {
          const endpoint = args[1];
          const method = args[args.indexOf('--method') + 1] || 'GET';
          
          if (endpoint.includes('/pulls/123/files')) {
            return { status: 0, stdout: JSON.stringify([{ filename: 'test.py' }]), stderr: '' };
          }
          if (endpoint.includes('/contents/test.py')) {
            return { status: 0, stdout: JSON.stringify({
              content: Buffer.from('        data = pickle.loads(user_input)').toString('base64')
            }), stderr: '' };
          }
          if (endpoint.includes('/pulls/123/comments') && method === 'GET') {
            return { status: 0, stdout: '[]', stderr: '' };
          }
          if (endpoint.includes('/pulls/123/reviews') && method === 'POST') {
            if (options && options.input) {
              capturedReviewData = JSON.parse(options.input);
            }
            return { status: 0, stdout: '{}', stderr: '' };
          }
          return { status: 0, stdout: '{}', stderr: '' };
        }
        return { status: 0, stdout: '{}', stderr: '' };
      });

      await import('./comment-pr-findings.js')
      expect(capturedReviewData).toBeDefined();
      expect(capturedReviewData.comments[0].body).toContain('🤖 **Security Issue: Insecure pickle loads**');
    });
  });

  describe('Finding Limits', () => {
    test('should process all ClaudeCode findings without limit', async () => {
      // Create 8 ClaudeCode findings
      const mockFindings = [];
      for (let i = 1; i <= 8; i++) {
        mockFindings.push({
          file: `test${i}.py`,
          line: 10,
          message: `Finding ${i}`,
          severity: 'HIGH',
          metadata: {
            vulnerability_type: 'security_issue',
            tool: 'ClaudeCode AI Security Analysis',
            check_id: `check-${i}`
          }
        });
      }

      const mockPrFiles = mockFindings.map(f => ({
        filename: f.file,
        patch: '@@ -10,1 +10,1 @@'
      }));

      readFileSyncSpy.mockImplementation((path) => {
        if (path.includes('github-event.json')) {
          return JSON.stringify({
            pull_request: { number: 123, head: { sha: 'abc123' } }
          });
        }
        if (path === 'findings.json') {
          return JSON.stringify(mockFindings);
        }
      });

      let capturedReviewData;
      spawnSyncSpy.mockImplementation((cmd, args, options) => {
        if (cmd === 'gh' && args.includes('api')) {
          const endpoint = args[1];
          const method = args[args.indexOf('--method') + 1] || 'GET';
          
          if (endpoint.includes('/pulls/123/files')) {
            return { status: 0, stdout: JSON.stringify(mockPrFiles), stderr: '' };
          }
          if (endpoint.includes('/pulls/123/comments') && method === 'GET') {
            return { status: 0, stdout: '[]', stderr: '' };
          }
          if (endpoint.includes('/pulls/123/reviews') && method === 'POST') {
            if (options && options.input) {
              capturedReviewData = JSON.parse(options.input);
            }
            return { status: 0, stdout: '{}', stderr: '' };
          }
          return { status: 0, stdout: '{}', stderr: '' };
        }
        return { status: 0, stdout: '{}', stderr: '' };
      });

      await import('./comment-pr-findings.js');
      
      expect(capturedReviewData).toBeDefined();
      expect(capturedReviewData.comments).toHaveLength(8); // Should process all 8 findings
      expect(consoleLogSpy).toHaveBeenCalledWith('Created review with 8 inline comments');
    });


    test('should handle findings with all required fields', async () => {
      // Create a ClaudeCode finding with all fields
      const mockFindings = [{
        file: 'test.py',
        line: 10,
        message: 'Insecure pickle usage detected',
        severity: 'HIGH',
        metadata: {
          vulnerability_type: 'security_issue',
          tool: 'ClaudeCode AI Security Analysis',
          check_id: 'pickle-insecure-usage'
        }
      }];

      const mockPrFiles = [{
        filename: 'test.py',
        patch: '@@ -10,1 +10,1 @@'
      }];

      readFileSyncSpy.mockImplementation((path) => {
        if (path.includes('github-event.json')) {
          return JSON.stringify({
            pull_request: { number: 123, head: { sha: 'abc123' } }
          });
        }
        if (path === 'findings.json') {
          return JSON.stringify(mockFindings);
        }
      });

      let capturedReviewData;
      spawnSyncSpy.mockImplementation((cmd, args, options) => {
        if (cmd === 'gh' && args.includes('api')) {
          const endpoint = args[1];
          const method = args[args.indexOf('--method') + 1] || 'GET';
          
          if (endpoint.includes('/pulls/123/files')) {
            return { status: 0, stdout: JSON.stringify(mockPrFiles), stderr: '' };
          }
          if (endpoint.includes('/pulls/123/comments') && method === 'GET') {
            return { status: 0, stdout: '[]', stderr: '' };
          }
          if (endpoint.includes('/pulls/123/reviews') && method === 'POST') {
            if (options && options.input) {
              capturedReviewData = JSON.parse(options.input);
            }
            return { status: 0, stdout: '{}', stderr: '' };
          }
          return { status: 0, stdout: '{}', stderr: '' };
        }
        return { status: 0, stdout: '{}', stderr: '' };
      });

      await import('./comment-pr-findings.js');
      
      expect(capturedReviewData).toBeDefined();
      expect(capturedReviewData.comments).toHaveLength(1);
      
      const comment = capturedReviewData.comments[0];
      expect(comment.body).toContain('🤖 **Security Issue:');
      expect(comment.body).toContain('**Severity:** HIGH');
      expect(comment.body).toContain('**Category:** security_issue');
      expect(comment.body).toContain('**Tool:** ClaudeCode AI Security Analysis');
      expect(consoleLogSpy).toHaveBeenCalledWith('Created review with 1 inline comments');
    });
  });

  describe('Error Handling', () => {
    test('should handle GitHub API errors gracefully', async () => {
     
      readFileSyncSpy.mockImplementation((path) => {
        if (path.includes('github-event.json')) {
          return JSON.stringify({
            pull_request: { number: 123, head: { sha: 'abc123' } }
          });
        }
        if (path === 'findings.json') {
          return JSON.stringify([{
            path: 'test.py',
            start: { line: 10 },
            check_id: 'rules.insecure-pickle-loads-autofix',
            extra: { message: 'Test', fix: 'test' }
          }]);
        }
      });

      spawnSyncSpy.mockImplementation((cmd, args, options) => {
        if (cmd === 'gh' && args.includes('api')) {
          const endpoint = args[1];
          if (endpoint.includes('/pulls/123/files')) {
            throw new Error('API rate limit exceeded');
          }
          return { status: 0, stdout: '{}', stderr: '' };
        }
        return { status: 0, stdout: '{}', stderr: '' };
      });

      await import('./comment-pr-findings.js')

      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to comment on PR:', expect.any(Error));
      expect(processExitSpy).toHaveBeenCalledWith(1);
    });

    test('should skip files not in PR diff', async () => {
      const mockFindings = [{
        path: 'not-in-diff.py',
        start: { line: 10 },
        check_id: 'rules.insecure-pickle-loads-autofix',
        extra: { message: 'Test', fix: 'test' }
      }];

      readFileSyncSpy.mockImplementation((path) => {
        if (path.includes('github-event.json')) {
          return JSON.stringify({
            pull_request: { number: 123, head: { sha: 'abc123' } }
          });
        }
        if (path === 'findings.json') {
          return JSON.stringify(mockFindings);
        }
      });

      spawnSyncSpy.mockImplementation((cmd, args, options) => {
        if (cmd === 'gh' && args.includes('api')) {
          const endpoint = args[1];
          if (endpoint.includes('/pulls/123/files')) {
            return { status: 0, stdout: JSON.stringify([{ filename: 'other-file.py' }]), stderr: '' };
          }
          return { status: 0, stdout: '{}', stderr: '' };
        }
        return { status: 0, stdout: '{}', stderr: '' };
      });

      await import('./comment-pr-findings.js');
      expect(consoleLogSpy).toHaveBeenCalledWith('File not-in-diff.py not in PR diff, skipping');
      expect(consoleLogSpy).toHaveBeenCalledWith('No findings to comment on PR diff');
    });
  });
});