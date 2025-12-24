import http.server
import socketserver
from crypto_utils import encrypt_payment

PORT = 8000

SECRET_KEY = "630be963-59e2-447a-8f3b-93b3d7a3bf25"


class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):

        # SAME AS PHP SAMPLE
        unique_id = "123"
        amount = "100"

        payment = encrypt_payment(unique_id, amount)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Python WebXPay Sample</title>
        </head>
        <body>
            <h2>WebXPay Python Sample Checkout</h2>

            <form action="https://stagingxpay.info/index.php?route=checkout/billing" method="POST">

                First name: <input type="text" name="first_name" value="My"><br>
                Last name: <input type="text" name="last_name" value="Face"><br>
                Email: <input type="text" name="email" value="notavailable@nawaloka.com"><br>
                Contact Number: <input type="text" name="contact_number" value="0771231234"><br>

                CMS: <input type="text" name="cms" value="Python"><br>
                custom: <input type="text" name="custom_fields" value=""><br><br>

                <input type="hidden" name="secret_key" value="{SECRET_KEY}">
                <textarea name="payment" rows="5" cols="70">{payment}</textarea><br><br>

                Version: <input type="text" name="version" value="5.2"><br>

                <input type="submit" value="Pay Now">
            </form>
        </body>
        </html>
        """

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print("Server running at http://localhost:8000")
        httpd.serve_forever()
