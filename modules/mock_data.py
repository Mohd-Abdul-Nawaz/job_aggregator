"""
mock_data.py
------------
Provides a realistic, diverse mock dataset of job/internship listings so
the whole pipeline (matching, sorting, filtering, apply-button UI) can be
demoed without needing a live scraper connected yet.

In production, replace `get_mock_jobs()` with real scraper/API outputs
that conform to the SAME column schema -- everything downstream
(matching_engine, filters, app.py) is written against this schema only,
not against any specific source site, so swapping in real data requires
no changes to the rest of the app.

Schema (one row per job/internship):
    title              str
    company            str
    source_site        str   -- e.g. "LinkedIn", "Internshala", "Company Careers Page"
    apply_url          str
    location            str
    country            str
    job_type           str   -- "Fresher / Entry-Level" or "Experienced"
    is_internship       bool
    has_ppo             bool  -- Pre-Placement Offer available
    compensation        int   -- monthly stipend or annual CTC in local currency units
    compensation_currency str
    min_cpi_required    float -- minimum CPI/GPA (on a 10-point scale) the employer asks for
    grad_year_required   int  -- target graduation year employer is hiring for
    description         str
    requirements         str
    posted_date          str
"""

import pandas as pd


def get_mock_jobs() -> pd.DataFrame:
    jobs = [
        dict(
            title="Software Development Intern",
            company="Nimbus Cloud Systems",
            source_site="Internshala",
            apply_url="https://internshala.com/internship/detail/example-1",
            location="Bengaluru, India",
            country="India",
            job_type="Fresher / Entry-Level",
            is_internship=True,
            has_ppo=True,
            compensation=25000,
            compensation_currency="INR",
            min_cpi_required=7.0,
            grad_year_required=2027,
            description=(
                "Work with our backend team to build and scale REST APIs used by "
                "our core product. You'll collaborate with senior engineers on "
                "microservices written in Python (FastAPI) and contribute to "
                "database schema design in PostgreSQL. This internship has a "
                "strong track record of converting into full-time offers."
            ),
            requirements=(
                "Currently pursuing B.Tech in Computer Science or related field. "
                "Familiarity with Python, basic understanding of REST APIs and SQL. "
                "Exposure to Git and version control. Strong problem-solving skills. "
                "Minimum CPI of 7.0."
            ),
            posted_date="2026-08-10",
        ),
        dict(
            title="Frontend Engineer (Entry Level)",
            company="Pixelworks Media",
            source_site="LinkedIn",
            apply_url="https://www.linkedin.com/jobs/view/example-2",
            location="Remote",
            country="Remote / Global",
            job_type="Fresher / Entry-Level",
            is_internship=False,
            has_ppo=False,
            compensation=600000,
            compensation_currency="INR",
            min_cpi_required=6.5,
            grad_year_required=2026,
            description=(
                "Join our product team to build delightful, accessible web "
                "interfaces using React and TypeScript. You'll work closely with "
                "designers to translate Figma mockups into pixel-perfect, "
                "responsive components, and own performance optimization for our "
                "customer-facing dashboard."
            ),
            requirements=(
                "B.Tech/B.E in any engineering discipline, graduating in 2026. "
                "Hands-on projects using React, HTML/CSS, and JavaScript. "
                "Understanding of responsive design and basic accessibility "
                "principles. Portfolio or GitHub link required."
            ),
            posted_date="2026-08-15",
        ),
        dict(
            title="Data Analyst Intern",
            company="Meridian Analytics",
            source_site="Naukri",
            apply_url="https://www.naukri.com/job-listings-example-3",
            location="Pune, India",
            country="India",
            job_type="Fresher / Entry-Level",
            is_internship=True,
            has_ppo=False,
            compensation=18000,
            compensation_currency="INR",
            min_cpi_required=7.5,
            grad_year_required=2027,
            description=(
                "Support the analytics team in building dashboards and reports "
                "for client engagements. Tasks include data cleaning in Python/"
                "pandas, writing SQL queries against our data warehouse, and "
                "building visualizations in Power BI to communicate insights to "
                "stakeholders."
            ),
            requirements=(
                "Pursuing a degree in Computer Science, Statistics, or related "
                "quantitative field. Working knowledge of Python (pandas, numpy), "
                "SQL, and basic statistics. Power BI or Tableau experience is a "
                "plus. Minimum CPI 7.5."
            ),
            posted_date="2026-08-05",
        ),
        dict(
            title="Machine Learning Engineer",
            company="Solaris AI Labs",
            source_site="Company Careers Page",
            apply_url="https://solarisai.example.com/careers/ml-engineer",
            location="Hyderabad, India",
            country="India",
            job_type="Experienced",
            is_internship=False,
            has_ppo=False,
            compensation=1800000,
            compensation_currency="INR",
            min_cpi_required=0.0,
            grad_year_required=2024,
            description=(
                "Design, train, and deploy ML models for our computer vision "
                "pipeline. You will own the full lifecycle: data preprocessing, "
                "model experimentation with PyTorch, and productionizing models "
                "via Docker and Kubernetes on GCP."
            ),
            requirements=(
                "2+ years of experience building and deploying ML models in "
                "production. Strong Python skills, deep familiarity with PyTorch "
                "or TensorFlow, and experience with cloud infra (GCP/AWS). "
                "MLOps exposure preferred."
            ),
            posted_date="2026-07-28",
        ),
        dict(
            title="Cloud Infrastructure Intern (with PPO)",
            company="Vertex Networks",
            source_site="Internshala",
            apply_url="https://internshala.com/internship/detail/example-5",
            location="Gurgaon, India",
            country="India",
            job_type="Fresher / Entry-Level",
            is_internship=True,
            has_ppo=True,
            compensation=30000,
            compensation_currency="INR",
            min_cpi_required=7.2,
            grad_year_required=2027,
            description=(
                "Get hands-on with real production cloud infrastructure. You'll "
                "help automate deployments using Terraform and Ansible, monitor "
                "systems with Prometheus/Grafana, and shadow the SRE on-call "
                "rotation. Top performers receive a full-time PPO."
            ),
            requirements=(
                "B.Tech students (CSE/IT/ECE) graduating 2027 with minimum CPI "
                "7.2. Basic Linux command-line skills, understanding of "
                "networking fundamentals, and any exposure to AWS/Azure/GCP is a "
                "bonus."
            ),
            posted_date="2026-08-20",
        ),
        dict(
            title="Backend Developer - Node.js",
            company="Fintrust Payments",
            source_site="Indeed",
            apply_url="https://www.indeed.com/viewjob?jk=example-6",
            location="Mumbai, India",
            country="India",
            job_type="Experienced",
            is_internship=False,
            has_ppo=False,
            compensation=1200000,
            compensation_currency="INR",
            min_cpi_required=0.0,
            grad_year_required=2023,
            description=(
                "Own backend services powering our payments platform, built in "
                "Node.js and Express, backed by MongoDB and Redis. You'll work "
                "on high-throughput transaction processing with strong emphasis "
                "on reliability and security."
            ),
            requirements=(
                "3+ years professional experience with Node.js and RESTful "
                "service design. Experience with MongoDB, Redis, and message "
                "queues (Kafka/RabbitMQ). Understanding of PCI-DSS or similar "
                "security compliance is a plus."
            ),
            posted_date="2026-07-15",
        ),
        dict(
            title="Product Design Intern",
            company="Loop Studio",
            source_site="AngelList (Wellfound)",
            apply_url="https://wellfound.com/jobs/example-7",
            location="Remote",
            country="Remote / Global",
            job_type="Fresher / Entry-Level",
            is_internship=True,
            has_ppo=False,
            compensation=800,
            compensation_currency="USD",
            min_cpi_required=0.0,
            grad_year_required=2026,
            description=(
                "Join a small, fast-moving design team building consumer mobile "
                "apps. You'll conduct user research, produce wireframes and "
                "high-fidelity prototypes in Figma, and run usability tests with "
                "real users."
            ),
            requirements=(
                "Design portfolio showcasing UX/UI work (student projects "
                "welcome). Proficiency in Figma. Strong communication skills; "
                "any coursework in HCI or psychology is a plus."
            ),
            posted_date="2026-08-01",
        ),
        dict(
            title="Embedded Systems Engineer (New Grad)",
            company="Orion Robotics",
            source_site="Company Careers Page",
            apply_url="https://orionrobotics.example.com/careers/embedded-newgrad",
            location="Bengaluru, India",
            country="India",
            job_type="Fresher / Entry-Level",
            is_internship=False,
            has_ppo=False,
            compensation=900000,
            compensation_currency="INR",
            min_cpi_required=7.0,
            grad_year_required=2026,
            description=(
                "Design and implement firmware for our autonomous robotics "
                "platform. You'll write C/C++ for ARM microcontrollers, "
                "integrate sensor data over I2C/SPI, and debug real-time control "
                "loops on physical hardware."
            ),
            requirements=(
                "B.Tech in ECE/EEE/Mechatronics, graduating 2026, minimum CPI "
                "7.0. Strong C/C++ fundamentals, understanding of "
                "microcontrollers (STM32/Arduino), and basic control systems "
                "knowledge."
            ),
            posted_date="2026-08-12",
        ),
        dict(
            title="DevOps Intern",
            company="Cascade Systems",
            source_site="LinkedIn",
            apply_url="https://www.linkedin.com/jobs/view/example-9",
            location="Chennai, India",
            country="India",
            job_type="Fresher / Entry-Level",
            is_internship=True,
            has_ppo=True,
            compensation=22000,
            compensation_currency="INR",
            min_cpi_required=6.8,
            grad_year_required=2027,
            description=(
                "Support our platform team in building CI/CD pipelines using "
                "GitHub Actions, containerizing services with Docker, and "
                "maintaining our staging Kubernetes cluster."
            ),
            requirements=(
                "B.Tech students graduating 2027, minimum CPI 6.8. Basic "
                "knowledge of Linux, Git, and any scripting language (Bash/"
                "Python). Coursework or personal projects with Docker are a "
                "plus."
            ),
            posted_date="2026-08-18",
        ),
        dict(
            title="Full Stack Developer",
            company="Bramble Retail Tech",
            source_site="Naukri",
            apply_url="https://www.naukri.com/job-listings-example-10",
            location="Delhi NCR, India",
            country="India",
            job_type="Experienced",
            is_internship=False,
            has_ppo=False,
            compensation=1400000,
            compensation_currency="INR",
            min_cpi_required=0.0,
            grad_year_required=2022,
            description=(
                "Build customer-facing e-commerce features end-to-end using "
                "React on the frontend and Django on the backend, with "
                "PostgreSQL as the primary datastore. Own features from design "
                "through deployment."
            ),
            requirements=(
                "2-4 years experience with React and Django (or similar Python "
                "web framework). Solid understanding of relational databases and "
                "REST API design. Experience with AWS deployment is a plus."
            ),
            posted_date="2026-07-20",
        ),
        dict(
            title="Quantitative Research Intern",
            company="Argent Capital",
            source_site="Company Careers Page",
            apply_url="https://argentcapital.example.com/careers/quant-intern",
            location="Mumbai, India",
            country="India",
            job_type="Fresher / Entry-Level",
            is_internship=True,
            has_ppo=True,
            compensation=50000,
            compensation_currency="INR",
            min_cpi_required=8.0,
            grad_year_required=2027,
            description=(
                "Research and backtest systematic trading strategies using "
                "historical market data. Heavy use of Python (pandas, numpy) "
                "and statistical modeling. Strong PPO conversion rate for "
                "top performers."
            ),
            requirements=(
                "Strong quantitative background (Math/Stats/CS/Engineering), "
                "graduating 2027 with minimum CPI 8.0. Proficiency in Python "
                "and statistics; knowledge of financial markets is a plus but "
                "not required."
            ),
            posted_date="2026-08-22",
        ),
        dict(
            title="QA Automation Engineer",
            company="Ferrous Systems India",
            source_site="Indeed",
            apply_url="https://www.indeed.com/viewjob?jk=example-12",
            location="Pune, India",
            country="India",
            job_type="Experienced",
            is_internship=False,
            has_ppo=False,
            compensation=1000000,
            compensation_currency="INR",
            min_cpi_required=0.0,
            grad_year_required=2023,
            description=(
                "Build and maintain our automated test suite using Selenium "
                "and Playwright. Collaborate with developers to embed testing "
                "into our CI pipeline and reduce regression bugs shipped to "
                "production."
            ),
            requirements=(
                "2+ years experience in test automation using Selenium/"
                "Playwright with Python or Java. Understanding of CI/CD "
                "pipelines. ISTQB certification is a plus but not required."
            ),
            posted_date="2026-07-30",
        ),
    ]

    df = pd.DataFrame(jobs)
    return df
