#!/usr/bin/env python3
import os
import sys
import json
import datetime

# Try importing required packages
try:
    import requests
except ImportError:
    requests = None

try:
    import yaml
except ImportError:
    yaml = None

try:
    import dotenv
except ImportError:
    dotenv = None

# Colors for visual console output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

TICK = f"{GREEN}✓{RESET}"
CROSS = f"{RED}✗{RESET}"
WARN_CHAR = f"{YELLOW}⚠{RESET}"

def print_section(title):
    print(f"\n{BOLD}{BLUE}=== {title} ==={RESET}")

def main():
    print(f"{BOLD}Running Post-Restart Environment Smoke-Tests...{RESET}")
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    
    # 1. Load environment from ~/.hermes/.env
    env_path = os.path.expanduser("~/.hermes/.env")
    env_loaded = False
    env_dict = {}
    
    if os.path.exists(env_path):
        if dotenv:
            try:
                env_dict = dotenv.dotenv_values(env_path)
                env_loaded = True
            except Exception as e:
                print(f" {CROSS} Failed to parse .env using python-dotenv: {e}")
        else:
            # Fallback manual parsing if dotenv is not working
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            env_dict[k.strip()] = v.strip().strip("'\"")
                env_loaded = True
            except Exception as e:
                print(f" {CROSS} Failed to manually parse .env: {e}")
    else:
        print(f" {CROSS} .env file not found at {env_path}")

    # Initialize report
    report = {
        "timestamp": timestamp,
        "status": "FAIL",
        "results": {}
    }
    
    overall_pass = True

    # ----------------------------------------------------
    # Checkpoint 1: Crucial Path Availability
    # ----------------------------------------------------
    print_section("Checkpoint 1: Crucial Path Availability")
    vault_path = "/home/justin.guest/vault"
    vault_exists = os.path.exists(vault_path)
    vault_is_dir = os.path.isdir(vault_path) if vault_exists else False
    vault_writable = os.access(vault_path, os.W_OK) if vault_exists else False
    
    path_status = "PASS" if (vault_exists and vault_is_dir and vault_writable) else "FAIL"
    if path_status == "FAIL":
        overall_pass = False
        
    report["results"]["path_verification"] = {
        "status": path_status,
        "vault_exists": vault_exists,
        "vault_is_dir": vault_is_dir,
        "vault_writable": vault_writable
    }
    
    if vault_exists and vault_is_dir and vault_writable:
        print(f" {TICK} Vault path '{vault_path}' exists, is a directory, and is writable.")
    else:
        print(f" {CROSS} Vault path verification failed!")
        print(f"   - Exists: {vault_exists}")
        print(f"   - Is Directory: {vault_is_dir}")
        print(f"   - Writable: {vault_writable}")

    # ----------------------------------------------------
    # Checkpoint 2: Python Environment Integrity
    # ----------------------------------------------------
    print_section("Checkpoint 2: Python Environment Integrity")
    packages_to_check = {
        "requests": requests is not None,
        "yaml": yaml is not None,
        "dotenv": dotenv is not None
    }
    
    env_status = "PASS" if all(packages_to_check.values()) else "FAIL"
    if env_status == "FAIL":
        overall_pass = False
        
    report["results"]["python_environment"] = {
        "status": env_status,
        "packages": packages_to_check
    }
    
    for pkg, imported in packages_to_check.items():
        if imported:
            print(f" {TICK} Package '{pkg}' is installed and importable.")
        else:
            print(f" {CROSS} Package '{pkg}' is missing!")

    # ----------------------------------------------------
    # Checkpoint 3: External API Reachability/Status
    # ----------------------------------------------------
    print_section("Checkpoint 3: External API Reachability/Status")
    api_results = {}
    
    # Check if requests is available to make API calls
    if not requests:
        print(f" {CROSS} Skipping API checks: 'requests' library not available.")
        api_results["status"] = "FAIL"
        api_results["message"] = "requests library not available"
        overall_pass = False
    else:
        # Define API configurations
        apis = {
            "Todoist": {
                "key_var": "TODOIST_API_KEY",
                "method": "GET",
                "url": "https://api.todoist.com/rest/v2/projects",
                "fallback_url": "https://api.todoist.com/api/v1/projects",
                "headers": lambda k: {"Authorization": f"Bearer {k}"},
                "verifier": lambda r: r.status_code == 200
            },
            "Slack": {
                "key_var": "SLACK_USER_TOKEN",
                "method": "POST",
                "url": "https://slack.com/api/auth.test",
                "headers": lambda k: {"Authorization": f"Bearer {k}"},
                "verifier": lambda r: r.status_code == 200 and r.json().get("ok") is True
            },
            "Linear": {
                "key_var": "LINEAR_API_KEY",
                "method": "POST",
                "url": "https://api.linear.app/v1/graphql",
                "fallback_url": "https://api.linear.app/graphql",
                "json_payload": {"query": "{ viewer { id name } }"},
                "headers": lambda k: {"Authorization": k},
                "verifier": lambda r: r.status_code == 200 and "data" in r.json()
            },
            "Readwise": {
                "key_var": "READWISE_API_KEY",
                "method": "GET",
                "url": "https://readwise.io/api/v2/auth/",
                "headers": lambda k: {"Authorization": f"Token {k}"},
                "verifier": lambda r: r.status_code in (200, 204)
            },
            "OpenRouter": {
                "key_var": "OPENROUTER_API_KEY",
                "method": "GET",
                "url": "https://openrouter.ai/api/v1/models",
                "headers": lambda k: {"Authorization": f"Bearer {k}"},
                "verifier": lambda r: r.status_code == 200
            }
        }
        
        for name, cfg in apis.items():
            key = env_dict.get(cfg["key_var"])
            if not key:
                print(f" {CROSS} {name}: Missing key '{cfg['key_var']}' in .env")
                api_results[name] = {
                    "status": "FAIL",
                    "error": f"Missing key {cfg['key_var']}"
                }
                overall_pass = False
                continue
                
            url = cfg["url"]
            fallback_url = cfg.get("fallback_url")
            headers = cfg["headers"](key)
            method = cfg["method"]
            json_payload = cfg.get("json_payload")
            verifier = cfg["verifier"]
            
            # Helper to run the HTTP request
            def run_req(req_url):
                if method == "POST":
                    return requests.post(req_url, headers=headers, json=json_payload, timeout=5)
                else:
                    return requests.get(req_url, headers=headers, timeout=5)
                    
            try:
                # Try primary request
                resp = run_req(url)
                passed = verifier(resp)
                
                # If primary failed but we have a fallback_url, try fallback
                used_fallback = False
                fallback_status = None
                fallback_text = ""
                
                if not passed and fallback_url:
                    try:
                        fallback_resp = run_req(fallback_url)
                        passed = verifier(fallback_resp)
                        used_fallback = True
                        resp = fallback_resp
                        fallback_status = fallback_resp.status_code
                    except Exception as fe:
                        fallback_text = str(fe)
                
                status_str = "PASS" if passed else "FAIL"
                if status_str == "FAIL":
                    overall_pass = False
                    
                api_results[name] = {
                    "status": status_str,
                    "url_used": fallback_url if (used_fallback and passed) else url,
                    "status_code": resp.status_code,
                    "used_fallback": used_fallback
                }
                
                if passed:
                    fallback_info = f" (fallback {fallback_url})" if used_fallback else ""
                    print(f" {TICK} {name}: Connected successfully! Status {resp.status_code}{fallback_info}")
                else:
                    print(f" {CROSS} {name}: Verification failed. Status {resp.status_code}")
                    print(f"   - URL: {url}")
                    if fallback_url:
                        print(f"   - Fallback URL: {fallback_url} (Status: {fallback_status}, Error: {fallback_text})")
                    print(f"   - Response: {resp.text[:200]}")
                    
            except requests.exceptions.Timeout:
                print(f" {CROSS} {name}: Request timed out (5s limit exceeded)")
                api_results[name] = {
                    "status": "FAIL",
                    "error": "Timeout"
                }
                overall_pass = False
            except Exception as e:
                print(f" {CROSS} {name}: Request failed: {e}")
                api_results[name] = {
                    "status": "FAIL",
                    "error": str(e)
                }
                overall_pass = False
                
    report["results"]["external_apis"] = api_results
    
    # 4. Final Status and JSON write
    report["status"] = "PASS" if overall_pass else "FAIL"
    
    report_path = os.path.expanduser("~/.hermes/health_report.json")
    try:
        with open(report_path, "w") as rf:
            json.dump(report, rf, indent=2)
        print_section("Health Report Generated")
        print(f" {TICK} Detailed JSON health report saved to: {report_path}")
    except Exception as e:
        print_section("Health Report Error")
        print(f" {CROSS} Failed to write health report to {report_path}: {e}")
        
    print_section("Smoke Test Summary")
    if report["status"] == "PASS":
        print(f" {BOLD}{GREEN}OVERALL STATUS: PASS{RESET}")
        print(" All post-restart environment tests completed successfully.")
        sys.exit(0)
    else:
        print(f" {BOLD}{RED}OVERALL STATUS: FAIL{RESET}")
        print(" Some checkpoints failed. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
