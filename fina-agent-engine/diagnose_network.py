import socket
import sys

def check_host(host, port):
    print(f"🔍 Checking connectivity to {host}:{port}...")
    try:
        # Step 1: Resolve DNS
        print(f"   [1/2] Resolving DNS...")
        ip = socket.gethostbyname(host)
        print(f"   ✅ DNS Resolved: {ip}")
        
        # Step 2: Connect via Socket
        print(f"   [2/2] Opening Socket...")
        with socket.create_connection((host, port), timeout=10):
            print(f"   ✅ Socket Connection: SUCCESS")
            return True
    except socket.gaierror as e:
        print(f"   ❌ DNS Resolution FAILED: {e}")
    except Exception as e:
        print(f"   ❌ Socket Connection FAILED: {e}")
    return False

if __name__ == "__main__":
    project_id = "srcqabgxibdshuwbkmcr"
    # Test base domain
    check_host(f"{project_id}.supabase.co", 443)
    # Test DB domain
    check_host(f"db.{project_id}.supabase.co", 5432)
