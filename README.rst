cmtucla_arXiv
=============

A tool to automate arXiv scraping.

Instructions
------------

* make sure that the ``path`` variable in ``main.py`` is the correct location of this project
* create a folder with your name in the directory ``users``
* add a file ``config.csv`` with your name and the email address through which you want to receive the arxiv mailing (copy from ``users/bart`` and adapt)
* add a file ``categories.txt`` with your arxiv categories (copy from ``users/bart`` and adapt)
* add a file ``keywords.txt`` with your keywords (copy from ``users/bart`` and adapt)
* add a file ``keyauthors.txt`` with your keyauthors (copy from ``users/bart`` and adapt)
* run ``python main.py`` to recieve an email summary from cmtucla.arxiv@gmail.com

Tips
----

* Do not leave trailing blank lines in input files

Dummy e-mail account
--------------------

This e-mail account is used to provide an smtp server to send the emails.

* Address: cmtucla.arxiv@gmail.com
* Password: hnKgqFpn2wPpBr9

Google doc
----------

A separate spreadsheet of useful arXiv articles is maintained at the link below:

https://docs.google.com/spreadsheets/d/1JZnc8O7RcHeAS07HiHUyWxLWf4fWyy49euT-tjuJLL8/edit?usp=sharing
