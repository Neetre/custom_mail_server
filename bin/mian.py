import os
import asyncore
import smtpd
import threading


class MailServer:
    def __init__(self, domain='example.com', smtp_port=25, pop3_port=110, mail_dir='./mailbox'):
        """
        Initialize mail server with domain and routing capabilities
        
        :param domain: Domain name for the mail server
        :param smtp_port: Port for SMTP server
        :param pop3_port: Port for POP3 server
        :param mail_dir: Directory to store emails
        """
        self.domain = domain
        self.smtp_port = smtp_port
        self.pop3_port = pop3_port
        self.mail_dir = mail_dir

        os.makedirs(mail_dir, exist_ok=True)

        self.valid_addresses = set()
    
    def add_email_address(self, email_address):
        """
        Add a valid email address to the server
        
        :param email_address: Full email address to add (e.g., 'user@example.com')
        """
        if not email_address.endswith(f'@{self.domain}'):
            raise ValueError(f"Email must be in the {self.domain} domain")

        username = email_address.split('@')[0]

        user_dir = os.path.join(self.mail_dir, username)
        os.makedirs(user_dir, exist_ok=True)

        self.valid_addresses.add(email_address)
        print(f"Added email address: {email_address}")
    
    def validate_recipient(self, recipient):
        """
        Validate if a recipient email address is valid for this server
        
        :param recipient: Email address to validate
        :return: Boolean indicating if address is valid
        """
        return recipient in self.valid_addresses
    
    def start_smtp_server(self):
        """
        Start a custom SMTP server with domain-specific routing
        """
        class DomainSMTPServer(smtpd.SMTPServer):
            def __init__(self, localaddr, remoteaddr, mail_server):
                super().__init__(localaddr, remoteaddr)
                self.mail_server = mail_server
            
            def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
                valid_recipients = [
                    rcpt for rcpt in rcpttos 
                    if self.mail_server.validate_recipient(rcpt)
                ]
                
                if not valid_recipients:
                    print(f"No valid recipients for email from {mailfrom}")
                    return
                
                for recipient in valid_recipients:
                    username = recipient.split('@')[0]
                    
                    user_dir = os.path.join(self.mail_server.mail_dir, username)
                    os.makedirs(user_dir, exist_ok=True)

                    filename = f"{len(os.listdir(user_dir)) + 1}.eml"
                    filepath = os.path.join(user_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(data.encode('utf-8'))
                    
                    print(f"Email saved for {recipient}")
                
                return

        smtp_server = DomainSMTPServer(
            ('0.0.0.0', self.smtp_port), 
            None, 
            self
        )
        print(f"SMTP Server for {self.domain} running on port {self.smtp_port}")

        smtp_thread = threading.Thread(target=asyncore.loop, kwargs={'timeout': 1})
        smtp_thread.start()
    
    def run(self):
        """
        Start the mail server
        """
        self.start_smtp_server()


if __name__ == "__main__":
    mail_server = MailServer(domain='example.com')
    mail_server.add_email_address('alice@example.com')
    mail_server.add_email_address('bob@example.com')

    mail_server.run()

    import time
    while True:
        time.sleep(1)