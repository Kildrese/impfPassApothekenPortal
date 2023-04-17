import os
import csv
import email
import imaplib

sender_email = os.getenv("SENDER_EMAIL")
password = os.getenv("SENDER_PASSWORD")
server = os.getenv("SENDER_IMAP")

mail = imaplib.IMAP4_SSL(server)
mail.login(sender_email, password)


# This function checks for non-existing mails and writes them to a csv file
def check_wrong_mails(df):
    # we choose the inbox but you can select others
    mail.select('inbox')

    status, data = mail.search(None, '(SUBJECT "Mail delivery failed")')
    # the list returned is a list of bytes separated
    # by white spaces on this format: [b'1 2 3', b'4 5 6']
    # so, to separate it first we create an empty list
    mail_ids = []
    # then we go through the list splitting its blocks
    # of bytes and appending to the mail_ids list
    for block in data:
        # the split function called without parameter
        # transforms the text or bytes into a list using
        # as separator the white spaces:
        # b'1 2 3'.split() => [b'1', b'2', b'3']
        mail_ids += block.split()

    # now for every id we'll fetch the email
    # to extract its content
    for i in mail_ids:
        # the fetch function fetch the email given its id
        # and format that you want the message to be
        status, data = mail.fetch(i, '(RFC822)')

        # the content data at the '(RFC822)' format comes on
        # a list with a tuple with header, content, and the closing
        for response_part in data:
            # so if its a tuple...
            if isinstance(response_part, tuple):
                # we go for the content at its second element
                # skipping the header at the first and the closing
                # at the third
                message = email.message_from_bytes(response_part[1])

                # then for the text we have a little more work to do
                # because it can be in plain text or multipart
                # if its not plain text we need to separate the message
                # from its annexes to get the text
                if message.is_multipart():
                    mail_content = ''

                    # on multipart we have the text message and
                    # another things like annex, and html version
                    # of the message, in that case we loop through
                    # the email payload
                    for part in message.get_payload():
                        # if the content type is text/plain
                        # we extract it
                        if part.get_content_type() == 'text/plain':
                            mail_content += part.get_payload()
                else:
                    # if the message isn't multipart, just extract it
                    mail_content = message.get_payload()

                from_mail = mail_content.split("To: ", 1)[1]
                wrong_mail = from_mail.split("\n", 1)[0]

                try:
                    index = df[df['Mail'] == wrong_mail.strip()].index.values[0]
                    print("Wrong mail at: " + str(index))

                    with open(os.getenv("WRONGFUL_MAILS_CSV"), 'a') as falsch:
                        wrong_writer = csv.writer(falsch, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                        wrong_writer.writerow(df.iloc[index])
                except IndexError:
                    print("not in data set")
