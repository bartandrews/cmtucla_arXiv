#####

# Inspired by:
# https://github.com/mahdisadjadi/arxivscraper
# https://github.com/blairbilodeau/arxiv-biorxiv-search
# Thank you to arXiv for use of its open access interoperability
######################################################################

# Packages
import datetime
import os
import xml.etree.ElementTree as ET
import gc
import pandas as pd
import smtplib, ssl
import sys
import numpy as np
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
try: #python3
    from urllib.request import urlopen
except: #python2
    from urllib2 import urlopen


# Custom exception if no submissions were found
class SubmissionError(Exception):
    pass

# Arxiv Bulletin class
class arxivbulletin:

    def __init__(self, myconfig, keywords, keyauthors):
        # Begin of timespan
        self.start = datetime.date.today()
        # End of timespan
        self.end = datetime.date.today()
        # Path to current directory
        self.path = os.getcwd()

        # Open and read (if possible) user provided search keywords
        self.keywords = keywords#self.openfile('keywords.txt')
        self.keyauthors = keyauthors#self.openfile('keyauthors.txt')
        # Open and read (if possible) user provided data
        self.name = myconfig["name"]
        self.email = myconfig["email"]
        self.sender = 'cmtucla.arxiv@gmail.com'
        self.password = 'hnKgqFpn2wPpBr9'
        self.categories = myconfig["categories"]
        # Get submissions for selected timespan and categories
        self.get_submissions()

        # If keywords and keyauthors are not provided by the user, collect all submissions
        if len(self.keywords) == 0 and len(self.keyauthors) == 0:
            self.records_df_filtered = self.records_df
            self.num_records_filtered = len(self.records_df_filtered)
            print("Submissions were not filtered, provide keywords or authors")
        else:
            # Filter by keywords and keyauthors
            self.filter()


    def openfile(self, fn):
        # open and read from user provided files
        try:
            results = []
            with open(os.path.join(os.path.split(self.path)[0], fn)) as f:
                for line in f:
                    results.append(line.strip())
            return results
        # if files do not exist, create empty array
        except IOError:
            results = []
            return results

    def extract_data(self, metadata, key):
        # extract human readable text from metadata
        ARXIV = '{http://arxiv.org/OAI/arXivRaw/}'
        return [meta.find(ARXIV + key).text.strip().replace('\n', ' ') for meta in metadata]

    def extract_authorlist(self, metadata):
        ARXIV = '{http://arxiv.org/OAI/arXivRaw/}'

        return [meta.find(ARXIV + 'authors').text.strip().lower().replace('\n', ' ') for meta in metadata]

    def get_submissions(self):

        OAI = '{http://www.openarchives.org/OAI/2.0/}'
        ARXIV = '{http://arxiv.org/OAI/arXivRaw/}'

        records_df = pd.DataFrame(columns=['title','abstract', 'abstract_title_concats', 'url','authors', 'date_v1'])

        for cat in self.categories:
            # Fetch from arXiv API for each category
            url = 'http://export.arxiv.org/oai2?verb=ListRecords&from=' + str(self.start) + '&until=' + str(self.end) + '&metadataPrefix=arXivRaw&set=' + cat
            data = urlopen(url)
            xml = data.read() # get raw xml data from server
            gc.collect()
            xml_root = ET.fromstring(xml)
            records = xml_root.findall(OAI + 'ListRecords/' + OAI + 'record') # list of all records from xml tree

            ## extract metadata for each record
            metadata = [record.find(OAI + 'metadata').find(ARXIV + 'arXivRaw') for record in records]

            ## use metadata to get info for each record
            titles = self.extract_data(metadata, 'title')
            abstracts = self.extract_data(metadata, 'abstract')
            urls = ['https://arxiv.org/abs/' + link for link in self.extract_data(metadata, 'id')]
            date_v1_submission = [str(datetime.datetime.strptime(meta.find(ARXIV + 'version').find(ARXIV + 'date').text, '%a, %d %b %Y %H:%M:%S %Z').date()) for meta in metadata]
            author_lists = self.extract_authorlist(metadata)
            abstract_title_concats = [title.lower() +'. '+abstract.lower() for title,abstract in zip(titles,abstracts)]

            ## compile all info into big dataframe
            records_data = list(zip(titles, abstracts, abstract_title_concats, urls, author_lists, date_v1_submission))
            records_df_tmp = pd.DataFrame(records_data,columns=['title','abstract', 'abstract_title_concats', 'url','authors', 'date_v1'])

            # Append to existing dataframe
            records_df = records_df.append(records_df_tmp, ignore_index=True)

        # If just interested in one day, exclude replacements
        if self.end == self.start:
            # Include up to a week in advance for submissions created earlier, yet exclude replacements
            datelist = [str(datetime.date.today()- datetime.timedelta(days=i)) for i in range(8)]
            # Filter based on last few days
            date_idxs = set([idx for idx,val in enumerate(list(map(lambda x: any([date in x for date in datelist]), records_df.date_v1))) if val])
            self.records_df = records_df.iloc[list(date_idxs)]
        else:
            self.records_df = records_df


        self.num_records = len(self.records_df)



    def filter(self):

        # Check for entries matching keywords, authors and dates
        kwd_idxs = set([idx for idx,val in enumerate(list(map(lambda x: any([kwd in x for kwd in self.keywords]), self.records_df.abstract_title_concats))) if val])
        auth_idxs = set([idx for idx,val in enumerate(list(map(lambda x: any([auth in x for auth in self.keyauthors]), self.records_df.authors))) if val])

        # Combine criteria
        idxs = set.union(kwd_idxs,auth_idxs)
        label = np.zeros(self.num_records)
        label[list(idxs)] = 1

        # Filter data
        self.records_df_filtered = self.records_df.iloc[list(idxs)]
        self.num_records_filtered = len(self.records_df_filtered)
        self.filter_idxs = label


    def create_report(self):
        # If there are no submissions, raise error and stop
        if self.num_records == 0:
            raise SubmissionError()

        # Get time span or date
        if self.end != self.start:
            timespan = "from " + str(self.start) + " to " + str(self.end)
        else:
            timespan = "for " + str(self.end)


        # Set up email message
        message = MIMEMultipart("alternative")
        message["Subject"] = "ArXiv summary " + timespan
        message["From"] = self.email
        message["To"] = self.email

        # Create the plain-text and HTML version of the message
        text = "Dear " + self.name +",\n" + "Today there were " + str(self.num_records) +" preprints on arXiv, out of which " + str(self.num_records_filtered) + " were relevant for you.\n" + u'\u2500' * 10 + "\n"

        # Add papers
        for i in range(self.num_records_filtered):
            header = " ".join(self.records_df_filtered.iloc[i].title.title().split()) + "\n" + "\n"
            body = self.records_df_filtered.iloc[i].abstract+ "\n"
            link = self.records_df_filtered.iloc[i].url + "\n"
            delimiter = u'\u2500' * 10 + "\n"
            text+=header+body+link+delimiter

        html = "<html><body><p>Dear " + self.name +",<br>Today there were "+str(self.num_records)+" preprints for " + ', '.join(self.categories) + " on arXiv, out of which "+str(self.num_records_filtered)+" were relevant for you.<br><hr></p>"""
        # Add papers
        for i in range(self.num_records_filtered):
            header = "<p><a href=" + self.records_df_filtered.iloc[i].url + ">" + " ".join(self.records_df_filtered.iloc[i].title.title().split()) + "</a><br>"
            authors = "<i>" + self.records_df_filtered.iloc[i].authors.title() + "</i><br><br>"
            body = self.records_df_filtered.iloc[i].abstract+ "<br><hr></p>"
            html+=header+authors+body
        html += "</body></html>"

        # Turn these into plain/html MIMEText objects
        try: #python3
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
        except: #python2.7
            part1 = MIMEText(text.encode('utf-8'), "plain")
            part2 = MIMEText(html.encode('utf-8'), "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(part1)
        message.attach(part2)

        return message, text

    # Send email using python 3
    def send_email_p3(self, message):
        port = 465  # For SSL
        # Create a secure SSL context
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            # Login
            server.login(self.sender, self.password)
            # Send message
            server.sendmail(self.sender, self.email, message.as_string())

    # Send email using python 2.7
    def send_email_p27(self, message):
        port = 465  # For SSL
        # Create a secure SSL context
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL("smtp.gmail.com", port)
        # Login
        server.login(self.sender, self.password)
        # Send message
        server.sendmail(self.sender, self.email, message.as_string())
        server.quit()

    def send_report(self):
        # if no email address stored, print to terminal
        if self.email is None:
            try:
                message, text = self.create_report()
                print(text)

            except SubmissionError:
                sys.stderr.write('No ArXiv submissions for selected timespan! \n')
                exit(-1)

        # if no password stored, ask user for access
        elif self.password is None:
            try:
                message, text = self.create_report()

            except SubmissionError:
                sys.stderr.write('No ArXiv submissions for selected timespan! \n')
                exit(-1)

            self.password = input("Type your e-mail password and press enter: ")

            try: #python3
                self.send_email_p3(message)
            except: #python2.7
                self.send_email_p27(message)


        # if email and password given, send message
        else:
            try:
                message, text = self.create_report()

            except SubmissionError:
                sys.stderr.write('No ArXiv submissions for selected timespan! \n')
                exit(-1)

            try: #python3
                self.send_email_p3(message)
            except: #python2.7
                self.send_email_p27(message)

    def save(self, filenamerec="arxivrecords.csv", filenamefil="arxivfilters.csv"):
        # Store collected arxiv papers
        with open(filenamerec, 'a') as f:
            self.records_df.to_csv(f, header=f.tell()==0)
        # Store indexes of selected entries
        with open(filenamefil, 'a') as f:
            np.savetxt(f, self.filter_idxs, '%s', ',')
