# Tunnel via Burp
If you want to tunnel the program over Burp i would recommend to use a virtualenv.
Then run `python3 -m certifi` to get the certificate path.
Export Burps cert. Transform it into pem format `openssl x509 -inform der -in burp_cert.der -out burp_cert.pem`
And then add it to the trusted root certs.
Make sure to run the following command while the virtual env is active.
`cat burp_cert.pem >> $(python3 -m certifi)`
Last but not least uncomment the proxy environment vars in `.env`.