# Phase 2 – Written explanation

Chapter 1 of the Phase 2 submission.

---

During the development phase I built EduFinance as a web application with a React frontend, a Flask
REST API and a PostgreSQL database. All parts run in Docker containers, and the current version is
hosted on a virtual machine in Microsoft Azure.

Before I started programming, I went through the feedback on my Phase 1 submission and reworked the
project plan, the requirements and the architecture documents (see chapter 2). After that I worked
in three sprints, following Scrum. At the end of every sprint I had a working version that I tested
and tagged in Git. Sprint 1 covered registration, life phases, wallets and transactions in different
currencies. In Sprint 2 I added money transfers, the monthly plan with the earning target, the loan
planner and the runway warnings. Sprint 3 brought the reports, the dashboard, the data export, a
demo account and the cloud deployment.

For the backend I kept the layered structure from my Phase 1 building block diagram. The routes only
receive and answer requests, and all calculations are in a separate service layer, which made it
possible to test them on their own. Money values are stored as exact decimals, and each transaction
keeps the exchange rate of the day it was entered, so older reports do not change later. The main
design decisions are written down as architecture decision records.

Some requirements changed once I used the app with realistic data, for example the way loans are
handled. I recorded these as change requests. While creating the demo data I also found a bug in the
exchange rate cache, which I fixed and covered with a test. At the end of the phase there are 102
backend tests and 32 frontend tests. Points that are still open are listed in chapter 9.
