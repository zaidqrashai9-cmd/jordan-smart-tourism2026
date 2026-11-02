# Remember Gemini key on Windows

Enter the key in the masked translation field and select حفظ المفتاح على هذا الجهاز, or click حفظ / تحديث المفتاح المحفوظ. Relaunching loads it automatically. Use نسيان المفتاح المحفوظ to delete the saved file and clear this session's field.

Storage: %LOCALAPPDATA%/JordanTourismMonitor/gemini-key.dpapi, outside the distributed application directory. Windows DPAPI CryptProtectData uses the current user scope (not LOCAL_MACHINE) and disables UI prompts. Only encrypted bytes are atomically written. Failure never falls back to plaintext. No new dependencies or administrator privileges required. Copying the app directory does not copy the stored key. Each colleague can save their own key. DPAPI does not protect against malware or other programs running as the same Windows user. Removing a local saved key does not revoke it at Google.

CI performs real Windows DPAPI encryption/decryption, verifies plaintext absence in stored bytes, deletion, corrupt-file handling, and failure-before-write. Local non-Windows runs skip the two DPAPI-specific tests. Production API credentials are never used in tests.
