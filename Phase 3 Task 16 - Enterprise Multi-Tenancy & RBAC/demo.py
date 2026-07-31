"""Task 16 — Live demo.  Run: python demo.py"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from tenancy.tenant_manager import (load_config, TenantStore, tenant_recommend,
                                     run_leakage_tests, KNOWN_TENANTS)

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

def main():
    sep("STEP 1 — Two tenants, one codebase, different configs")
    for tid in ["google", "microsoft"]:
        cfg = load_config(tid)
        print(f"  {tid:<12}: threshold={cfg['matching_threshold']}  "
              f"skill_w={cfg['skill_weight']}  exp_w={cfg['experience_weight']}  "
              f"model={cfg.get('model_version','default')}")
    print("\n  Same code path for both. Config source:")
    print(f"    google    → {load_config('google')['_source']}")
    print(f"    microsoft → {load_config('microsoft')['_source']}")

    sep("STEP 2 — Google: tenant-scoped inference (own data only)")
    g_store = TenantStore("google")
    student_g = g_store.candidates[0]
    g_result  = tenant_recommend("google", student_g["student_id"])
    print(f"  Student : {g_result['student_name']} (Google tenant)")
    print(f"  Scope   : {g_result['data_scope']}")
    print(f"  Threshold used: {g_result['threshold']}")
    for r in g_result["recommendations"]:
        print(f"    #{r['score']:.3f}  {r['title']:<28}  {r['company']}")

    sep("STEP 3 — Microsoft: same student profile, different config → different results")
    # Use Microsoft's first candidate for a fair comparison
    m_store  = TenantStore("microsoft")
    student_m = m_store.candidates[0]
    m_result  = tenant_recommend("microsoft", student_m["student_id"])
    print(f"  Student : {m_result['student_name']} (Microsoft tenant)")
    print(f"  Scope   : {m_result['data_scope']}")
    print(f"  Threshold used: {m_result['threshold']}")
    for r in m_result["recommendations"]:
        print(f"    #{r['score']:.3f}  {r['title']:<28}  {r['company']}")
    print("\n  → Different threshold, different job pool, different results.")
    print("    Zero code changes. Config only.")

    sep("STEP 4 — Google tries to access Microsoft's candidate (leakage test)")
    g_store2 = TenantStore("google")
    ms_candidate = m_store.candidates[0]
    result = g_store2.cross_tenant_access("microsoft", ms_candidate["student_id"])
    print(f"  Status  : {result['status']}")
    print(f"  Reason  : {result['reason']}")

    sep("STEP 5 — All 6 cross-tenant leakage tests")
    tests = run_leakage_tests()
    print(f"  {'Requesting':<12} {'Target':<12} {'Candidate':<18} {'Result'}")
    for t in tests:
        icon = "✓ BLOCKED" if t["pass"] else "✗ LEAKED"
        print(f"  {t['requesting_tenant']:<12} {t['target_tenant']:<12} "
              f"{t['student_name']:<18} {icon}")
    all_pass = all(t["pass"] for t in tests)
    print(f"\n  All {len(tests)} leakage tests PASSED: {all_pass}")

    sep("STEP 6 — FAILURE SCENARIO A: unknown tenant ID")
    try:
        TenantStore("unknown_corp")
    except PermissionError as e:
        print(f"  PermissionError: {e}")
    print("  → System rejects unknown tenants at the door. No data exposed.")

    sep("STEP 7 — FAILURE SCENARIO B: missing config → safe default fallback")
    cfg = load_config("unknown_tenant_xyz")
    print(f"  Config source: {cfg['_source']}")
    print(f"  Threshold: {cfg['matching_threshold']} (default, not another tenant's config)")
    print("  → System falls back to default.yaml. Never borrows another tenant's settings.")

    sep("DEMO COMPLETE")
    print("  Reports: tenant_isolation_report.md, leakage_test.csv,")
    print("           tenant_config_report.csv, evaluation_report.csv")

if __name__ == "__main__":
    main()
