import os
import csv
import requests
import json
import traceback
import datetime

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# base dir
base_dir = os.path.dirname(os.path.abspath(__file__))

# review shake api token
spiderman_token = "aeb256bfba92a5bdf5d2fb6c3866d25759ccb52c"

# review shake api header
headers = {
    'spiderman-token': spiderman_token,
    }

# get groups that api account has
def get_groups():
    url = "https://app.datashake.com/api/v2/profiles/job_groups"
    response = requests.request("GET", url, headers=headers)
    response_dict = json.loads(response.text)
    return response_dict["job_groups"]

# resync all groups
def resync_groups(groups_list):
    # loop all groups
    for group in groups_list:
        url = "https://app.datashake.com/api/v2/profiles/job_groups/{}/resync".format(group["id"])
        querystring = {}
        response = requests.request("POST", url, headers=headers, params=querystring)
        response_dict = json.loads(response.text)
        print("Your job group {} has been queued for resync".format(group["id"]))

# get group reviews
def get_group_reviews(group_id):
    # Yesterday date 
    today = datetime.date.today() 
    yesterday = today - datetime.timedelta(days = 1)
    url = "https://app.datashake.com/api/v2/profiles/job_groups/{}/reviews".format(group_id)
    querystring = { "from_date" : '2020-08-01' }
    response = requests.request("GET", url, headers=headers, params=querystring)
    response_dict = json.loads(response.text)
    reviews = response_dict["reviews"]
    return reviews

# change date format from YYYY-mm-dd to mm-dd-YYYY
def change_date_format(ymd_date):
    return datetime.datetime.strptime(ymd_date, "%Y-%m-%d").strftime("%m-%d-%Y")

# send email
def send_email(reviews_list, group_name):
    try:
        from_mail = "test@parity-analytics.net"
        to_mail = list() # must be a list

        receivers_csv = "{}/resources/receivers.csv".format(base_dir)
        if os.path.isfile(receivers_csv):
            with open(receivers_csv, 'r') as receiver_csv:
                reader = csv.DictReader(receiver_csv, fieldnames=['Receiver Email', 'Group Names'])
                for row in reader:
                    if row["Receiver Email"] == "Receiver Email":
                        continue

                    if any(group_name == item.strip() for item in row["Group Names"].split(',')):
                        to_mail.append(row["Receiver Email"].strip())
        
        # make html body
        html_body = ""
        if reviews_list:
            for review in reviews_list:
                html_body += "<p style='margin:0;'><strong>Business Name</strong> : %s</p>" % (group_name,)
                html_body += "<p style='margin:0;'><strong>Date</strong> : %s</p>" % (change_date_format(review["date"]),)
                html_body += "<p style='margin:0;'><strong>Rating</strong> : %s</p>" % (review["rating_value"],)
                html_body += "<p style='margin:0;'><strong>Name</strong> : %s</p>" % (review["name"],)
                html_body += "<p style='margin:0;'><strong>Text</strong> : %s</p>" % (review["review_text"],)
                html_body += "<br>"
        else:
            html_body = "Not Exist New Review at Yesterday."
            
        subject = 'Reviews of Group {}'.format(group_name)
        html = ''

        # make html
        html = """
        <html>
        <head></head>
        <body>
            %s
        </body>
        </html>
        """ % ( html_body,)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_mail
        msg['To'] = to_mail[0]

        part1=MIMEText(html, 'html')

        msg.attach(part1)

        # Send the mail
        server = smtplib.SMTP('mail.parity-analytics.net', 587)
        server.ehlo()
        server.starttls()
        server.login(from_mail, "test1234")
        server.sendmail(from_mail, to_mail, msg.as_string())
        server.quit()
    except:
        print(traceback.print_exc())
    return


def main():
    # Get Groups (part 2 - 1,2)
    groups_list = get_groups()
    
    # if groups exist
    if groups_list:

        # Resync Groups (part 2 - 3)
        # resync_groups(groups_list)

        for group in groups_list:
            # Get Group Reviews(part 2 - 4, 5)
            reviews_list = get_group_reviews(group["id"])
            
            # Send Group reviews via email
            send_email(reviews_list, group["name"])

    
    else:
        print("Please check your groups. Can't find any group.")

if __name__ == '__main__':
    main()