"""
User Acceptance Test for SpendSense.
Usage:
  uv run python3 scripts/uat_test.py
  uv run python3 scripts/uat_test.py --url https://YOUR-BACKEND.up.railway.app
"""
import requests, sys, random, string
from datetime import date

BASE = sys.argv[sys.argv.index("--url") + 1] if "--url" in sys.argv else "http://localhost:8000"
PASS = True

def ok(msg):           print(f"  PASS: {msg}")
def fail(msg, d=""):
    global PASS
    PASS = False
    print(f"  FAIL: {msg} {d}")
def rand_email():      return "uat_" + "".join(random.choices(string.ascii_lowercase, k=8)) + "@test.com"
def get_token(e, pw):
    r = requests.post(f"{BASE}/auth/login", json={"email": e, "password": pw})
    return r.json().get("access_token") if r.ok else None
def H(tok):            return {"Authorization": f"Bearer {tok}"}

print(f"\nRunning UAT against {BASE}\n")

# T1 Health
print("T1: Health")
ok("health 200") if requests.get(f"{BASE}/health").ok else fail("health")

# T2 Registration
print("T2: Registration")
e1, e2 = rand_email(), rand_email()
ok("register user1") if requests.post(f"{BASE}/auth/register", json={"email": e1, "password": "Pass123!"}).status_code == 201 else fail("register user1")
ok("register user2") if requests.post(f"{BASE}/auth/register", json={"email": e2, "password": "Pass123!"}).status_code == 201 else fail("register user2")
ok("duplicate rejected") if requests.post(f"{BASE}/auth/register", json={"email": e1, "password": "Pass123!"}).status_code == 400 else fail("duplicate email")

# T3 Login
print("T3: Login")
t1, t2 = get_token(e1, "Pass123!"), get_token(e2, "Pass123!")
ok("user1 login") if t1 else fail("user1 login")
ok("user2 login") if t2 else fail("user2 login")
ok("wrong password 401") if requests.post(f"{BASE}/auth/login", json={"email": e1, "password": "wrong"}).status_code == 401 else fail("wrong pw")

# T4 Data isolation
print("T4: Data isolation")
requests.post(f"{BASE}/expenses/manual", headers=H(t1),
              json={"vendor": "IsolationTest", "amount": 99, "category": "Food"})
month = date.today().strftime("%Y-%m")
exps1 = [e["vendor"] for e in requests.get(f"{BASE}/expenses/{month}", headers=H(t1)).json()]
exps2 = [e["vendor"] for e in requests.get(f"{BASE}/expenses/{month}", headers=H(t2)).json()]
ok("user1 sees own expense")         if "IsolationTest" in exps1     else fail("user1 data missing")
ok("user2 cannot see user1 expense") if "IsolationTest" not in exps2 else fail("DATA ISOLATION BREACH")

# T5 AI parsing
print("T5: AI parsing")
ok("parse") if requests.post(f"{BASE}/expenses/parse", headers=H(t1), json={"text": "coffee 120"}).ok else fail("parse")

# T6 Input validation
print("T6: Validation")
ok("negative amount rejected") if requests.post(f"{BASE}/expenses/manual", headers=H(t1), json={"vendor": "X", "amount": -1, "category": "Food"}).status_code == 422 else fail("negative amount")
ok("vendor too long rejected") if requests.post(f"{BASE}/expenses/manual", headers=H(t1), json={"vendor": "A" * 101, "amount": 1, "category": "Food"}).status_code == 422 else fail("vendor length")

# T7 CSV export
print("T7: CSV export")
r = requests.get(f"{BASE}/export/csv/all", headers=H(t1))
ok("csv export") if r.ok and "text/csv" in r.headers.get("content-type", "") else fail("csv", r.status_code)

# T8 Onboarding
print("T8: Onboarding")
me = requests.get(f"{BASE}/auth/me", headers=H(t1)).json()
ok("onboarding_complete field present") if "onboarding_complete" in me else fail("field missing")
ok("complete-onboarding") if requests.post(f"{BASE}/auth/complete-onboarding", headers=H(t1)).ok else fail("complete-onboarding")

# T9 Security headers
print("T9: Security headers")
hdrs = requests.get(f"{BASE}/health").headers
for h in ["x-content-type-options", "x-frame-options", "strict-transport-security"]:
    ok(h) if h in hdrs else fail(f"missing {h}")

# T10 Cleanup
print("T10: Cleanup")
for tok in [t1, t2]:
    if tok:
        requests.delete(f"{BASE}/auth/account", headers=H(tok), json={"confirmation": "DELETE"})
ok("test users deleted")

print(f"\n{'ALL TESTS PASSED' if PASS else 'SOME TESTS FAILED'}\n")
sys.exit(0 if PASS else 1)
