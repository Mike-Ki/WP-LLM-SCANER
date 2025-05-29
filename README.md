## Tunneling a Program Over Burp Suite

To tunnel a program over Burp Suite, it's recommended to use a Python `virtualenv`. Follow these steps:

1. **Create and activate a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2. **Get the certificate path used by `certifi`**:
    ```bash
    python3 -m certifi
    ```

3. **Export Burp's certificate** (e.g., from your browser or Burp directly), then convert it to PEM format:
    ```bash
    openssl x509 -inform DER -in burp_cert.der -out burp_cert.pem
    ```

4. **Add the Burp certificate to the trusted root certificates**.
   Make sure your virtual environment is still active, then run:
    ```bash
    cat burp_cert.pem >> $(python3 -m certifi)
    ```

5. **Uncomment the proxy environment variables in your `.env` file** to route traffic through Burp.

---

This setup allows your Python application to trust Burp's certificate when intercepting HTTPS traffic.

