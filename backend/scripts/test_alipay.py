# -*- coding: utf-8 -*-
"""
Alipay Sandbox Payment Diagnostic Script
Run: python test_alipay.py
Verifies Alipay sandbox configuration
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")
from config import settings
from alipay import AliPay


def test_alipay_config():
    print("=" * 60)
    print("Alipay Sandbox Config Diagnostic")
    print("=" * 60)

    # 1. Check configuration
    print("\n[1] Current Config:")
    print(f"    APP_ID:        {settings.ALIPAY_APP_ID}")
    print(f"    NOTIFY_URL:    {settings.ALIPAY_NOTIFY_URL}")
    print(f"    RETURN_URL:    {settings.ALIPAY_RETURN_URL}")
    print(f"    DEBUG:         {settings.ALIPAY_DEBUG}")
    print(f"    SIGN_TYPE:     RSA2")
    print(f"    GATEWAY:       https://openapi-sandbox.dl.alipaydev.com/gateway.do")

    # 2. Read keys
    print("\n[2] Key File Check:")
    try:
        with open(settings.ALIPAY_APP_PRIVATE_KEY_PATH, "r") as f:
            app_private_key = f.read().strip()
        print(f"    [OK] App Private Key: {settings.ALIPAY_APP_PRIVATE_KEY_PATH}")
        print(f"      Length: {len(app_private_key)} chars")
        print(f"      Head: {app_private_key[:50]}...")
    except Exception as e:
        print(f"    [FAIL] Cannot read private key: {e}")
        return

    try:
        with open(settings.ALIPAY_PUBLIC_KEY_PATH, "r") as f:
            alipay_public_key = f.read().strip()
        print(f"    [OK] Alipay Public Key: {settings.ALIPAY_PUBLIC_KEY_PATH}")
        print(f"      Length: {len(alipay_public_key)} chars")
        print(f"      Head: {alipay_public_key[:50]}...")
    except Exception as e:
        print(f"    [FAIL] Cannot read public key: {e}")
        return

    # 3. Create AliPay instance
    print("\n[3] Create AliPay Instance:")
    try:
        alipay = AliPay(
            appid=settings.ALIPAY_APP_ID,
            app_notify_url=settings.ALIPAY_NOTIFY_URL,
            app_private_key_string=app_private_key,
            alipay_public_key_string=alipay_public_key,
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG,
            verbose=True,
        )
        print("    [OK] AliPay instance created")
    except Exception as e:
        print(f"    [FAIL] AliPay creation failed: {e}")
        return

    # 4. Test signature generation
    print("\n[4] Test Payment Parameter Signing:")
    try:
        query_string = alipay.api_alipay_trade_page_pay(
            out_trade_no="TEST20260621001",
            total_amount="0.01",
            subject="Test Order",
            return_url=settings.ALIPAY_RETURN_URL,
            notify_url=settings.ALIPAY_NOTIFY_URL,
        )
        print(f"    [OK] Signature generated")
        print(f"    Query string length: {len(query_string)}")

        # Parse key params
        params = {}
        for pair in query_string.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                params[k] = v
        print(f"    method:      {params.get('method', 'N/A')}")
        print(f"    app_id:      {params.get('app_id', 'N/A')}")
        print(f"    sign_type:   {params.get('sign_type', 'N/A')}")
        print(f"    sign:        {params.get('sign', 'N/A')[:40]}...")
        print(f"    charset:     {params.get('charset', 'N/A')}")
    except Exception as e:
        print(f"    [FAIL] Signature generation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. Test self-verification
    print("\n[5] Test Signature Self-Verification:")
    try:
        from urllib.parse import unquote_plus
        sign = params.pop("sign", "")
        # URL-decode the signature (in real flow, Alipay does this)
        sign_decoded = unquote_plus(sign)
        verify_params = {}
        for k, v in params.items():
            verify_params[k] = v
        result = alipay.verify(verify_params, sign_decoded)
        if result:
            print("    [OK] Self-verification PASSED (local key pair matches)")
        else:
            print("    [FAIL] Self-verification FAILED (local key pair MISMATCH!)")
            print("    --> Check if app_private_key.pem and alipay_public_key.pem are a pair")
            print("    --> This is the #1 cause of 'sign check fail' on Alipay page")
    except Exception as e:
        print(f"    [FAIL] Verification error: {e}")
        import traceback
        traceback.print_exc()

    # 6. Summary
    print("\n" + "=" * 60)
    print("Diagnostic Summary")
    print("=" * 60)
    print(f"""
If all checks pass but payment still fails, verify:

1. [Alipay Sandbox Console] (https://open.alipay.com/develop/sandbox/app)
   - Is APP_ID correct: {settings.ALIPAY_APP_ID}
   - Is the application public key the same as keys/alipay_public_key.pem?
   - Is sign type set to RSA2?

2. [Sandbox Buyer Account]
   - Must use sandbox buyer account to pay (NOT real Alipay account)
   - Find sandbox buyer accounts in the sandbox console
   - You can top up sandbox account balance there

3. [Callback URL]
   - notify_url must be accessible from internet: {settings.ALIPAY_NOTIFY_URL}
   - 生产环境填服务器公网域名/IP；本地联调用内网穿透工具把本地端口映射到公网

4. [Common Error Codes]
   - "sign check fail" / "验签失败" → RSA key mismatch
   - "merchant info error" / "商户信息有误" → Wrong APP_ID
   - "merchant not exist" / "该商家不存在" → App not activated or wrong APP_ID
   - "buyer account not exist" / "买家账号不存在" → Using real Alipay account
   - "system busy" / "系统繁忙" → Parameter format error or sandbox maintenance
""")


if __name__ == "__main__":
    test_alipay_config()
