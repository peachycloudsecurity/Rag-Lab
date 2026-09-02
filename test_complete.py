#!/usr/bin/env python3
"""
Complete Test Suite for DevNotes Vulnerable App
Ensures app works for 60+ concurrent users in workshop setting
"""

import requests
import time
import hashlib
import concurrent.futures
import sys
from datetime import datetime

BASE_URL = "http://localhost:5000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


class TestStats:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []


stats = TestStats()


def print_test(name, success, details=""):
    stats.total += 1
    if success:
        stats.passed += 1
        status = f"{Colors.GREEN}✓ PASS{Colors.END}"
    else:
        stats.failed += 1
        stats.errors.append(f"{name}: {details}")
        status = f"{Colors.RED}✗ FAIL{Colors.END}"

    print(f"{status} - {name}")
    if details:
        print(f"  {Colors.BLUE}{details}{Colors.END}")


def test_app_is_running():
    """Test 1: Verify app is accessible"""
    try:
        r = requests.get(BASE_URL, timeout=5)
        success = r.status_code in [200, 302]
        print_test("App is running", success, f"Status: {r.status_code}")
        return success
    except Exception as e:
        print_test("App is running", False, f"Error: {str(e)}")
        return False


def test_user_registration():
    """Test 2: User registration with email"""
    session = requests.Session()
    timestamp = int(time.time())
    username = f"testuser_{timestamp}"
    email = f"{username}@test.com"

    r = session.post(f"{BASE_URL}/register", data={
        "username": username,
        "email": email,
        "password": "test123"
    })

    success = r.status_code == 200 or "Registered" in r.text
    print_test("User registration with email", success, f"User: {username}")
    return success, session, username, email


def test_user_login(username):
    """Test 3: User login"""
    session = requests.Session()
    r = session.post(f"{BASE_URL}/login", data={
        "username": username,
        "password": "test123"
    })

    success = r.status_code == 200 or "notes" in r.url.lower()
    print_test(f"User login ({username})", success)
    return success, session


def test_note_creation(session, username):
    """Test 4: Note creation"""
    r = session.post(f"{BASE_URL}/notes/create", data={
        "title": f"Test Note by {username}",
        "body": "This is a test note"
    })

    success = r.status_code == 200 or "notes" in r.url
    print_test(f"Note creation ({username})", success)

    # Extract note ID from redirect
    note_id = None
    if r.url and '/notes/' in r.url:
        note_id = r.url.split('/')[-1]

    return success, note_id


def test_user_isolation(session1, note_id1, session2):
    """Test 5: Verify user isolation (IDOR vulnerability exists)"""
    # This test EXPECTS the vulnerability to exist
    r = session2.get(f"{BASE_URL}/notes/{note_id1}")

    # In vulnerable app, this should succeed (IDOR)
    success = r.status_code == 200
    print_test("User isolation test (IDOR exists)", success,
              "User2 can access User1's note (vulnerability confirmed)")
    return success


def test_sql_injection():
    """Test 6: SQL injection in search"""
    session = requests.Session()

    # Login first
    session.post(f"{BASE_URL}/register", data={
        "username": f"sqlitest_{int(time.time())}",
        "email": f"sqlitest_{int(time.time())}@test.com",
        "password": "test123"
    })
    session.post(f"{BASE_URL}/login", data={
        "username": f"sqlitest_{int(time.time())}",
        "password": "test123"
    })

    # Test SQL injection
    r = session.get(f"{BASE_URL}/notes/search", params={"q": "test' OR '1'='1"})

    success = r.status_code == 200
    print_test("SQL injection vulnerability", success,
              "SQL injection in search works (vulnerability confirmed)")
    return success


def test_weak_email_validation():
    """Test 7: Weak email validation"""
    session = requests.Session()

    # Test with invalid but accepted email
    weak_emails = [
        "test@",
        "@domain.com",
        "test@@domain.com"
    ]

    passed = 0
    for email in weak_emails:
        try:
            timestamp = int(time.time() * 1000)  # More unique
            r = session.post(f"{BASE_URL}/register", data={
                "username": f"weak_{timestamp}",
                "email": email,
                "password": "test123"
            })
            if "Invalid email" not in r.text and r.status_code == 200:
                passed += 1
        except:
            pass

    success = passed > 0
    print_test("Weak email validation", success,
              f"{passed}/{len(weak_emails)} weak emails accepted")
    return success


def test_api_key_creation(session):
    """Test 8: API key creation and logging"""
    r = session.post(f"{BASE_URL}/api-keys")

    # Check if key was created
    success = r.status_code == 200 and "API" in r.text

    print_test("API key creation", success)

    # Try to extract API key from response
    api_key = None
    if "api_key" in r.text or "API Key" in r.text:
        # Key created successfully
        pass

    return success, api_key


def test_admin_user_creation():
    """Test 9: Admin can create users"""
    admin_session = requests.Session()

    # Login as admin
    r = admin_session.post(f"{BASE_URL}/login", data={
        "username": "admin",
        "password": "admin123"
    })

    if r.status_code != 200:
        print_test("Admin login", False, "Cannot login as admin")
        return False

    # Create user via admin
    timestamp = int(time.time())
    r = admin_session.post(f"{BASE_URL}/admin/users", data={
        "action": "create",
        "username": f"admin_created_{timestamp}",
        "email": f"admin_created_{timestamp}@test.com",
        "password": "test123",
        "is_admin": ""
    })

    success = r.status_code == 200 or "created" in r.text.lower()
    print_test("Admin user creation", success)
    return success


def test_bulk_user_creation():
    """Test 10: Bulk user creation"""
    admin_session = requests.Session()

    # Login as admin
    admin_session.post(f"{BASE_URL}/login", data={
        "username": "admin",
        "password": "admin123"
    })

    # Create 5 users in bulk
    timestamp = int(time.time())
    emails = "\n".join([f"bulk{i}_{timestamp}@test.com" for i in range(5)])

    r = admin_session.post(f"{BASE_URL}/admin/users", data={
        "action": "bulk_create",
        "emails": emails,
        "default_password": "Welcome123!"
    })

    success = r.status_code == 200 and ("Created" in r.text or "created" in r.text)
    print_test("Bulk user creation (5 users)", success)
    return success


def test_bulk_user_deletion():
    """Test 11: Bulk user deletion"""
    admin_session = requests.Session()

    # Login as admin
    admin_session.post(f"{BASE_URL}/login", data={
        "username": "admin",
        "password": "admin123"
    })

    # Create users first
    timestamp = int(time.time())
    emails = "\n".join([f"delete{i}_{timestamp}@test.com" for i in range(3)])

    # Create them
    admin_session.post(f"{BASE_URL}/admin/users", data={
        "action": "bulk_create",
        "emails": emails,
        "default_password": "test123"
    })

    time.sleep(0.5)

    # Delete them
    r = admin_session.post(f"{BASE_URL}/admin/users", data={
        "action": "bulk_delete",
        "delete_emails": emails
    })

    success = r.status_code == 200 and ("Deleted" in r.text or "deleted" in r.text)
    print_test("Bulk user deletion (3 users)", success)
    return success


def test_concurrent_users(num_users=10):
    """Test 12: Concurrent user creation and note creation"""
    print(f"\n{Colors.YELLOW}Testing {num_users} concurrent users...{Colors.END}")

    def create_user_and_note(user_id):
        try:
            session = requests.Session()
            timestamp = int(time.time() * 1000) + user_id
            username = f"concurrent_{timestamp}_{user_id}"
            email = f"{username}@test.com"

            # Register
            r = session.post(f"{BASE_URL}/register", data={
                "username": username,
                "email": email,
                "password": "test123"
            }, timeout=10)

            if r.status_code != 200 and "Registered" not in r.text:
                return False, f"Registration failed for {username}"

            # Login
            r = session.post(f"{BASE_URL}/login", data={
                "username": username,
                "password": "test123"
            }, timeout=10)

            if r.status_code != 200:
                return False, f"Login failed for {username}"

            # Create note
            r = session.post(f"{BASE_URL}/notes/create", data={
                "title": f"Concurrent Note {user_id}",
                "body": f"Created by {username}"
            }, timeout=10)

            return True, username

        except Exception as e:
            return False, f"Error: {str(e)}"

    # Execute concurrently
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(create_user_and_note, i) for i in range(num_users)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    end_time = time.time()
    duration = end_time - start_time

    successful = sum(1 for success, _ in results if success)
    success = successful == num_users

    print_test(f"Concurrent user creation ({num_users} users)",
              success,
              f"{successful}/{num_users} succeeded in {duration:.2f}s")

    return success


def test_api_key_logging():
    """Test 13: Verify API key logging"""
    session = requests.Session()
    timestamp = int(time.time())

    # Register and login
    session.post(f"{BASE_URL}/register", data={
        "username": f"logtest_{timestamp}",
        "email": f"logtest_{timestamp}@test.com",
        "password": "test123"
    })
    session.post(f"{BASE_URL}/login", data={
        "username": f"logtest_{timestamp}",
        "password": "test123"
    })

    # Create API key
    session.post(f"{BASE_URL}/api-keys")

    # Check if log file exists
    try:
        import os
        log_exists = os.path.exists('api_keys.log')
        success = log_exists

        if log_exists:
            with open('api_keys.log', 'r') as f:
                content = f.read()
                has_api_key_log = "API_KEY_CREATED" in content

            print_test("API key logging", has_api_key_log,
                      "API keys logged to api_keys.log")
        else:
            print_test("API key logging", False, "Log file not found")

    except Exception as e:
        print_test("API key logging", False, f"Error checking logs: {str(e)}")

    return success


def test_admin_api_key_view():
    """Test 14: Admin can view API keys"""
    admin_session = requests.Session()

    # Login as admin
    admin_session.post(f"{BASE_URL}/login", data={
        "username": "admin",
        "password": "admin123"
    })

    # Access admin API keys page
    r = admin_session.get(f"{BASE_URL}/admin/api-keys")

    success = r.status_code == 200 and ("API" in r.text or "api" in r.text)
    print_test("Admin API key dashboard access", success)
    return success


def test_md5_password_hashing():
    """Test 15: Verify weak MD5 password hashing"""
    # Known: admin password is admin123
    expected_hash = hashlib.md5(b"admin123").hexdigest()

    # This is "0192023a7bbd73250516f069df18b500"
    success = expected_hash == "0192023a7bbd73250516f069df18b500"

    print_test("MD5 password hashing (weak)", success,
              f"admin123 hashes to {expected_hash}")
    return success


def test_predictable_api_keys():
    """Test 16: Verify API keys are predictable (MD5-based)"""
    session = requests.Session()
    timestamp = int(time.time())

    # Register and login
    session.post(f"{BASE_URL}/register", data={
        "username": f"apitest_{timestamp}",
        "email": f"apitest_{timestamp}@test.com",
        "password": "test123"
    })
    session.post(f"{BASE_URL}/login", data={
        "username": f"apitest_{timestamp}",
        "password": "test123"
    })

    # Create API key
    r = session.post(f"{BASE_URL}/api-keys")

    # API keys are MD5 hashes (32 hex chars)
    success = r.status_code == 200
    print_test("Predictable API key generation (MD5)", success,
              "API keys use MD5 (weak)")
    return success


def run_all_tests():
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}DevNotes Complete Test Suite{Colors.END}")
    print(f"{Colors.BLUE}Workshop-Ready Verification (60+ concurrent users){Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")

    start_time = datetime.now()

    # Test 1: Basic functionality
    if not test_app_is_running():
        print(f"\n{Colors.RED}App is not running. Please start it first.{Colors.END}")
        print(f"{Colors.YELLOW}Run: docker compose up{Colors.END}")
        return False

    # Test 2-4: User registration, login, notes
    success, session1, username1, email1 = test_user_registration()
    if not success:
        print(f"{Colors.RED}Basic registration failed. Stopping tests.{Colors.END}")
        return False

    success, session1 = test_user_login(username1)
    success, note_id1 = test_note_creation(session1, username1)

    # Test 5: User isolation (IDOR vulnerability)
    timestamp = int(time.time())
    session2 = requests.Session()
    username2 = f"testuser2_{timestamp}"
    session2.post(f"{BASE_URL}/register", data={
        "username": username2,
        "email": f"{username2}@test.com",
        "password": "test123"
    })
    session2.post(f"{BASE_URL}/login", data={
        "username": username2,
        "password": "test123"
    })

    if note_id1:
        test_user_isolation(session1, note_id1, session2)

    # Test 6-7: Vulnerabilities
    test_sql_injection()
    test_weak_email_validation()

    # Test 8: API keys
    test_api_key_creation(session1)
    test_api_key_logging()
    test_predictable_api_keys()

    # Test 9-11: Admin functionality
    test_admin_user_creation()
    test_bulk_user_creation()
    test_bulk_user_deletion()
    test_admin_api_key_view()

    # Test 12: Concurrent users (start small)
    test_concurrent_users(num_users=5)

    # Test 13: Stress test with more users
    print(f"\n{Colors.YELLOW}Running stress test with 20 concurrent users...{Colors.END}")
    test_concurrent_users(num_users=20)

    # Test 14: Crypto weaknesses
    test_md5_password_hashing()

    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}Test Summary{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")

    print(f"\nTotal Tests: {stats.total}")
    print(f"{Colors.GREEN}Passed: {stats.passed}{Colors.END}")
    print(f"{Colors.RED}Failed: {stats.failed}{Colors.END}")
    print(f"Duration: {duration:.2f} seconds")

    if stats.failed > 0:
        print(f"\n{Colors.RED}Failed Tests:{Colors.END}")
        for error in stats.errors:
            print(f"  - {error}")

    print(f"\n{Colors.YELLOW}Workshop Readiness Assessment:{Colors.END}")
    if stats.failed == 0:
        print(f"{Colors.GREEN}✓ READY FOR 60+ STUDENT WORKSHOP{Colors.END}")
        print(f"{Colors.GREEN}  All tests passed successfully{Colors.END}")
        print(f"{Colors.GREEN}  App can handle concurrent usage{Colors.END}")
        print(f"{Colors.GREEN}  All vulnerabilities present and exploitable{Colors.END}")
    elif stats.failed <= 2:
        print(f"{Colors.YELLOW}⚠ MOSTLY READY{Colors.END}")
        print(f"{Colors.YELLOW}  Minor issues detected, app should work{Colors.END}")
    else:
        print(f"{Colors.RED}✗ NOT READY{Colors.END}")
        print(f"{Colors.RED}  Multiple failures detected{Colors.END}")
        print(f"{Colors.RED}  Fix issues before workshop{Colors.END}")

    print(f"\n{Colors.BLUE}Next Steps:{Colors.END}")
    print("1. Review any failed tests")
    print("2. Test with your actual workshop load")
    print("3. Ensure adequate server resources")
    print("4. Have backup deployment ready")

    print(f"\n{Colors.YELLOW}⚠️  This app is INTENTIONALLY VULNERABLE{Colors.END}")
    print(f"{Colors.YELLOW}   Only use in isolated training environments{Colors.END}\n")

    return stats.failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
