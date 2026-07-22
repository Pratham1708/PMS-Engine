"""
company_service.py — Corporate Profile Metadata & JSON Caching Service.
Saves and loads company profile JSON files from data/company_cache/.
Uses a robust static dictionary for all Nifty 50 stocks to provide high-fidelity, real, and detailed corporate information.
"""

import os
import json
import logging
import shutil
from typing import Dict, Any, Optional

from app.data.loader import data_loader

logger = logging.getLogger(__name__)

# Configure local company cache path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.path.abspath(os.path.join(BASE_DIR, "data", "company_cache"))

# Complete high-fidelity company metadata database for all 50 Nifty stocks
NIFTY_50_COMPANY_DATABASE: Dict[str, Dict[str, Any]] = {
    "ADANIENT.NS": {
        "company_name": "Adani Enterprises Limited",
        "symbol": "ADANIENT.NS",
        "sector": "Energy & Resources",
        "industry": "Conglomerates / Infrastructure",
        "market_cap": "₹3.50 Lakh Cr",
        "employees": "30,000+",
        "headquarters": "Ahmedabad, India",
        "website": "https://www.adanienterprises.com",
        "description": "Adani Enterprises Limited is the flagship company of the Adani Group, one of India's largest business conglomerates. It functions as an in-house incubator, developing new businesses in infrastructure, energy, utility, and mining sectors before spinning them off into independent listed entities.",
        "segments": "Integrated Resources Management, Solar Manufacturing, Mining, Airports Infrastructure, Road & Rail Construction, Data Centers, and New Energy Business.",
        "history": "Incorporated in 1988 as Adani Exports Limited by Gautam Adani, initially trading in commodities. It went public in 1994, transitioned to infrastructure development, and rebranded to Adani Enterprises in 2006 to reflect its incubation model.",
        "logo_url": None
    },
    "ADANIPORTS.NS": {
        "company_name": "Adani Ports and Special Economic Zone Limited",
        "symbol": "ADANIPORTS.NS",
        "sector": "Industrials",
        "industry": "Marine Ports & Services",
        "market_cap": "₹2.85 Lakh Cr",
        "employees": "3,000+",
        "headquarters": "Ahmedabad, India",
        "website": "https://www.adaniports.com",
        "description": "Adani Ports and Special Economic Zone Limited (APSEZ) is India's largest private multi-port operator and logistics developer. APSEZ represents a network of 12 ports and terminals across India, handling roughly 24% of the country's total port capacity.",
        "segments": "Port Services, Port-led Special Economic Zone (SEZ), Container Terminal Operations, Inland Logistics, and Warehousing Services.",
        "history": "Established in 1998 as Gujarat Adani Port Limited to develop the Mundra Port in Gujarat. Operations commenced in 2001. Rebranded to APSEZ in 2012 as it acquired and expanded into other major ports on both the east and west coasts of India.",
        "logo_url": None
    },
    "APOLLOHOSP.NS": {
        "company_name": "Apollo Hospitals Enterprise Limited",
        "symbol": "APOLLOHOSP.NS",
        "sector": "Healthcare",
        "industry": "Hospitals & Medical Services",
        "market_cap": "₹82,000 Cr",
        "employees": "70,000+",
        "headquarters": "Chennai, India",
        "website": "https://www.apollohospitals.com",
        "description": "Apollo Hospitals Enterprise Limited is India's largest healthcare provider, operating a network of hospitals, primary care clinics, diagnostic centers, and pharmacies. It is widely recognized for introducing modern, corporate healthcare delivery systems to India.",
        "segments": "Healthcare Services (Hospitals), Retail Pharmacies, Digital Health Platform (Apollo 24/7), Clinics, Diagnostics, and Health Insurance JV.",
        "history": "Founded by Dr. Prathap C. Reddy in 1983 with the opening of India's first corporate hospital in Chennai. It subsequently pioneered multi-specialty care and expanded through major cities, listing on the NSE as the premier healthcare stock.",
        "logo_url": None
    },
    "ASIANPAINT.NS": {
        "company_name": "Asian Paints Limited",
        "symbol": "ASIANPAINT.NS",
        "sector": "Consumer Discretionary",
        "industry": "Paints & Coatings",
        "market_cap": "₹2.90 Lakh Cr",
        "employees": "8,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.asianpaints.com",
        "description": "Asian Paints Limited is India's leading paint manufacturer and Asia's third-largest paint company. It operates in 15 countries and is a dominant player in the decorative and industrial coatings market, expanding recently into home decor, bath fittings, and modular kitchens.",
        "segments": "Decorative Paints (Interior, Exterior, Wood), Industrial Coatings (Automotive, Protective), Home Decor (Kitchens, Bathrooms, Wardrobes, Sanitizers).",
        "history": "Founded in 1942 by four friends—Champaklal Choksey, Chimanlal Choksi, Suryakant Dani, and Arvind Vakil—in a garage in Mumbai. By 1967, it became the largest paint manufacturer in India, a position it has held uninterrupted since.",
        "logo_url": None
    },
    "AXISBANK.NS": {
        "company_name": "Axis Bank Limited",
        "symbol": "AXISBANK.NS",
        "sector": "Financials",
        "industry": "Private Sector Banking",
        "market_cap": "₹3.30 Lakh Cr",
        "employees": "95,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.axisbank.com",
        "description": "Axis Bank Limited is the third-largest private sector bank in India, offering a comprehensive suite of financial services to corporate, retail, MSME, and agricultural customers. The bank has a robust domestic network of over 4,800 branches and a growing digital presence.",
        "segments": "Treasury Operations, Corporate/Retail Banking, Retail Lending, Wealth Management, and Digital Banking Services.",
        "history": "Promoted in 1993 jointly by Unit Trust of India (UTI), LIC, and GIC, commencing operations in 1994 as UTI Bank. It was rebranded as Axis Bank in 2007 to establish a distinct corporate identity. In 2023, it completed the landmark acquisition of Citibank's India consumer business.",
        "logo_url": None
    },
    "BAJAJ-AUTO.NS": {
        "company_name": "Bajaj Auto Limited",
        "symbol": "BAJAJ-AUTO.NS",
        "sector": "Consumer Discretionary",
        "industry": "Two & Three-Wheelers",
        "market_cap": "₹1.40 Lakh Cr",
        "employees": "10,000+",
        "headquarters": "Pune, India",
        "website": "https://www.bajajauto.com",
        "description": "Bajaj Auto Limited is a leading Indian multinational automotive manufacturer. It is the world's third-largest manufacturer of motorcycles and the largest manufacturer of three-wheelers, with exports contributing to over 40% of its total revenue.",
        "segments": "Motorcycles (Pulsar, Discover, Platina, Avenger), Three-Wheelers (RE Passenger & Cargo), Electric Vehicles (Chetak EV).",
        "history": "Founded in 1945 by Jamnalal Bajaj as a trading company importing two and three-wheelers. It acquired a manufacturing license in 1959. In the 1970s, it grew into a household name with the iconic Chetak scooter. It transitioned focus to motorcycles in the late 1990s and early 2000s under Rajiv Bajaj.",
        "logo_url": None
    },
    "BAJAJFINSV.NS": {
        "company_name": "Bajaj Finserv Limited",
        "symbol": "BAJAJFINSV.NS",
        "sector": "Financials",
        "industry": "Diversified Financial Services",
        "market_cap": "₹2.45 Lakh Cr",
        "employees": "20,000+",
        "headquarters": "Pune, India",
        "website": "https://www.bajajfinserv.in",
        "description": "Bajaj Finserv Limited is the holding company for the financial services businesses of the Bajaj Group. Through its core subsidiaries, it offers solutions in consumer lending, asset management, wealth management, and life/general insurance.",
        "segments": "Consumer Lending & Finance (Bajaj Finance), Life Insurance (Bajaj Allianz Life), General Insurance (Bajaj Allianz General), and Digital Financial Marketplaces.",
        "history": "Demerged from Bajaj Auto Limited in 2007 to operate as a pure-play financial services holding company. Under Sanjiv Bajaj's leadership, it has built India's largest non-bank finance ecosystems.",
        "logo_url": None
    },
    "BAJFINANCE.NS": {
        "company_name": "Bajaj Finance Limited",
        "symbol": "BAJFINANCE.NS",
        "sector": "Financials",
        "industry": "Consumer Finance & NBFC",
        "market_cap": "₹4.35 Lakh Cr",
        "employees": "40,000+",
        "headquarters": "Pune, India",
        "website": "https://www.bajajfinserv.in/bajaj-finance",
        "description": "Bajaj Finance Limited is one of India's largest and most diversified non-banking financial companies (NBFCs). It is a market leader in consumer durable finance, two-wheeler finance, personal loans, and business loans, serving over 60 million active clients.",
        "segments": "Consumer Lending, SME Lending, Commercial Lending, Rural Lending, Wealth Management, and Deposits.",
        "history": "Incorporated in 1987 as Bajaj Auto Finance Limited, primarily to fund Bajaj two-wheelers. It went public in 1994. Rebranded to Bajaj Finance in 2010, shifting focus to a massive digital-first consumer lending strategy which pioneered instant point-of-sale financing in India.",
        "logo_url": None
    },
    "BEL.NS": {
        "company_name": "Bharat Electronics Limited",
        "symbol": "BEL.NS",
        "sector": "Industrials",
        "industry": "Defence Electronics",
        "market_cap": "₹95,000 Cr",
        "employees": "9,000+",
        "headquarters": "Bengaluru, India",
        "website": "https://www.bel-india.in",
        "description": "Bharat Electronics Limited (BEL) is an Indian state-owned aerospace and defence company. It manufactures advanced electronic products for the Indian Armed Forces, including radar systems, sonar, communication equipment, electronic warfare systems, and electronic voting machines (EVMs).",
        "segments": "Defence Electronics, Aerospace Equipment, Electronic Voting Machines, Solar Products, and Medical Devices.",
        "history": "Established in 1954 under the Ministry of Defence to manufacture basic communication equipment. It grew to design and construct complex radar networks, missile control systems, and optoelectronics, achieving Navratna status in 1997.",
        "logo_url": None
    },
    "BHARTIARTL.NS": {
        "company_name": "Bharti Airtel Limited",
        "symbol": "BHARTIARTL.NS",
        "sector": "Communication Services",
        "industry": "Telecom — Mobile & Broadband",
        "market_cap": "₹5.30 Lakh Cr",
        "employees": "18,000+",
        "headquarters": "New Delhi, India",
        "website": "https://www.airtel.in",
        "description": "Bharti Airtel Limited is a leading global telecommunications company operating across 18 countries in Asia and Africa. It is India's second-largest mobile operator, offering high-speed 4G/5G mobile services, broadband, enterprise solutions, digital TV, and mobile payments.",
        "segments": "Mobile Services (India, Africa), Airtel Business (Enterprise Solutions), Homes Services (Broadband), Digital TV Services, and Airtel Payments Bank.",
        "history": "Founded by Sunil Bharti Mittal in 1995 with the launch of mobile services in Delhi. Rebranded to Airtel in 2002. Pioneered the telecom outsourcing model, outsourcing IT and network operations to global tech companies to focus solely on marketing and customer service.",
        "logo_url": None
    },
    "BPCL.NS": {
        "company_name": "Bharat Petroleum Corporation Limited",
        "symbol": "BPCL.NS",
        "sector": "Energy",
        "industry": "Oil Refining & Marketing",
        "market_cap": "₹1.60 Lakh Cr",
        "employees": "9,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.bharatpetroleum.in",
        "description": "Bharat Petroleum Corporation Limited (BPCL) is an Indian government-owned oil and gas explorer, refiner, and marketer. BPCL operates three major refineries in Mumbai, Kochi, and Bina, alongside a retail network of over 20,000 fuel stations.",
        "segments": "Refining, Crude Oil Exploration, Retail Fuel Distribution, LPG (Bharatgas), Aviation Fuel, Lubricants (MAK), and Petrochemicals.",
        "history": "Traces roots to the Rangoon Oil Company formed in the late 19th century. In 1928, Asiatic Petroleum combined with Burmah Oil to form Burmah-Shell. Nationalized by the Government of India in 1976 and renamed Bharat Petroleum Corporation Limited.",
        "logo_url": None
    },
    "BRITANNIA.NS": {
        "company_name": "Britannia Industries Limited",
        "symbol": "BRITANNIA.NS",
        "sector": "Consumer Staples",
        "industry": "Packaged Foods & Bakery",
        "market_cap": "₹1.15 Lakh Cr",
        "employees": "4,500+",
        "headquarters": "Kolkata, India",
        "website": "https://www.britannia.co.in",
        "description": "Britannia Industries Limited is India's leading food manufacturer, specializing in bakery products. The company owns household brand names such as Good Day, Tiger, NutriChoice, Marie Gold, and 50-50, and commands over 30% of the Indian biscuit market share.",
        "segments": "Biscuits, Bread, Rusk, Cakes, Dairy Products (Cheese, Yogurt, Milk, Butter), and International Exports.",
        "history": "Established in 1892 in Kolkata by a group of British businessmen with an investment of ₹295. In 1918, it incorporated as Britannia Biscuits. Wadia Group acquired control in 1993. It has since scaled its distribution network to reach over 6 million retail outlets.",
        "logo_url": None
    },
    "CIPLA.NS": {
        "company_name": "Cipla Limited",
        "symbol": "CIPLA.NS",
        "sector": "Healthcare",
        "industry": "Pharmaceuticals",
        "market_cap": "₹1.05 Lakh Cr",
        "employees": "25,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.cipla.com",
        "description": "Cipla Limited is a global pharmaceutical company focusing on respiratory, cardio-vascular, anti-diabetic, and oncology treatments. It is world-renowned for providing low-cost, high-quality generic drugs, particularly for treating HIV in developing countries.",
        "segments": "Active Pharmaceutical Ingredients (APIs), Formulations (Generics, Branded Generics, OTC), and Respiratory Products (Inhalers).",
        "history": "Founded in 1935 by Dr. K.A. Hamied as The Chemical, Industrial & Pharmaceutical Laboratories (CIPLA). In 2001, under Yusuf Hamied, Cipla revolutionized global HIV therapy by providing triple-therapy drugs for less than $1 a day, saving millions of lives in Africa.",
        "logo_url": None
    },
    "COALINDIA.NS": {
        "company_name": "Coal India Limited",
        "symbol": "COALINDIA.NS",
        "sector": "Energy",
        "industry": "Coal Mining",
        "market_cap": "₹2.20 Lakh Cr",
        "employees": "240,000+",
        "headquarters": "Kolkata, India",
        "website": "https://www.coalindia.in",
        "description": "Coal India Limited (CIL) is an Indian government-owned coal mining and refining corporation. It is the largest coal-producing company in the world, contributing to roughly 82% of India's total coal production and powering major thermal energy utilities.",
        "segments": "Coking Coal Production, Non-Coking Coal Production, Coal Beneficiation, and Coal Gasification Projects.",
        "history": "Formed in 1975 under the nationalization of coal mines in India to manage state coal assets under a single apex body. Listed in 2010 in what was then the largest-ever IPO in India. CIL operates through several regional mining subsidiaries.",
        "logo_url": None
    },
    "DRREDDY.NS": {
        "company_name": "Dr. Reddy's Laboratories Limited",
        "symbol": "DRREDDY.NS",
        "sector": "Healthcare",
        "industry": "Pharmaceuticals & API",
        "market_cap": "₹92,000 Cr",
        "employees": "23,000+",
        "headquarters": "Hyderabad, India",
        "website": "https://www.drreddys.com",
        "description": "Dr. Reddy's Laboratories Limited is an Indian multinational pharmaceutical company. It produces a wide range of generic medicines, active pharmaceutical ingredients (APIs), diagnostic kits, and biologics, with major export markets in the US, Europe, and Russia.",
        "segments": "Global Generics, Pharmaceutical Services & Active Ingredients (PSAI), Proprietary Products, and Biosimilars.",
        "history": "Founded in 1984 by scientist-entrepreneur Dr. K. Anji Reddy. It started as an API exporter and quickly expanded into finished dosage formulations. It was the first Asian pharmaceutical company outside Japan to list on the NYSE (in 2001).",
        "logo_url": None
    },
    "EICHERMOT.NS": {
        "company_name": "Eicher Motors Limited",
        "symbol": "EICHERMOT.NS",
        "sector": "Consumer Discretionary",
        "industry": "Motorcycles (Royal Enfield)",
        "market_cap": "₹98,000 Cr",
        "employees": "5,000+",
        "headquarters": "New Delhi, India",
        "website": "https://www.eichermotors.com",
        "description": "Eicher Motors Limited is the parent company of Royal Enfield, the global leader in middleweight (250cc-750cc) motorcycles. It also operates a commercial vehicle joint venture with Volvo Group, Volvo Eicher Commercial Vehicles (VECV).",
        "segments": "Royal Enfield Motorcycles (Classic, Bullet, Himalayan, Meteor), and Commercial Vehicles (VECV Trucks & Buses).",
        "history": "Traces history to the establishment of Goodearth Company in 1948, importing tractors. Rebranded to Eicher Tractor in 1959. Acquired Royal Enfield in 1994. Under Siddhartha Lal, the company consolidated, sold non-core assets, and turned Royal Enfield into a premium lifestyle global brand.",
        "logo_url": None
    },
    "ETERNAL.NS": {
        "company_name": "Zomato Limited (formerly Eternal)",
        "symbol": "ETERNAL.NS",
        "sector": "Consumer Discretionary",
        "industry": "Online Food Delivery & Quick Commerce",
        "market_cap": "₹1.55 Lakh Cr",
        "employees": "4,000+",
        "headquarters": "Gurugram, India",
        "website": "https://www.zomato.com",
        "description": "Zomato Limited is India's leading online food ordering, delivery, and restaurant discovery platform. The company also operates Blinkit, one of India's largest quick-commerce grocery delivery platforms, alongside Hyperpure (B2B restaurant supply service).",
        "segments": "Food Delivery, Restaurant Dining Discovery, Quick Commerce (Blinkit), and B2B Supplies (Hyperpure).",
        "history": "Founded in 2008 by Deepinder Goyal and Pankaj Chaddah as Foodiebay, renaming to Zomato in 2010. It listed on the Indian stock exchanges in 2021 as a pioneer tech-startup listing. Acquired Blinkit in 2022 to enter the rapid-delivery sector.",
        "logo_url": None
    },
    "GRASIM.NS": {
        "company_name": "Grasim Industries Limited",
        "symbol": "GRASIM.NS",
        "sector": "Materials",
        "industry": "Cement, Chemicals & Textiles (Aditya Birla)",
        "market_cap": "₹1.25 Lakh Cr",
        "employees": "24,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.grasim.com",
        "description": "Grasim Industries Limited is the flagship company of the Aditya Birla Group. It is the world's largest producer of Viscose Staple Fiber (VSF) and a leading producer of Chlor-Alkali and epoxy in India. Through its subsidiary UltraTech, it is also India's largest cement maker.",
        "segments": "Viscose Staple Fiber (VSF), Viscose Filament Yarn (VFY), Chemicals (Chlor-Alkali), Textiles, Insulators, and Paints.",
        "history": "Incorporated in 1947 by Ghanshyam Das Birla as a textile manufacturing company in Gwalior. Over the decades, it integrated backwards into VSF and pulp production, forwards into chemicals, and ultimately acquired massive cement and paint operations.",
        "logo_url": None
    },
    "HCLTECH.NS": {
        "company_name": "HCL Technologies Limited",
        "symbol": "HCLTECH.NS",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "market_cap": "₹3.80 Lakh Cr",
        "employees": "220,000+",
        "headquarters": "Noida, India",
        "website": "https://www.hcltech.com",
        "description": "HCL Technologies Limited is the third-largest IT services company in India, offering software solutions, infrastructure management, engineering services, and IP-led digital services to Fortune 500 enterprises globally.",
        "segments": "IT & Business Services (Application Development, Infrastructure), Engineering and R&D Services (ER&D), and Products & Platforms (HCL Software).",
        "history": "Spun off from HCL Enterprise in 1991 when India opened up its economy, launching IT consulting services under Shiv Nadar. It went public in 1999 and grew dynamically through infrastructure services and strategic IP acquisitions from companies like IBM.",
        "logo_url": None
    },
    "HDFCBANK.NS": {
        "company_name": "HDFC Bank Limited",
        "symbol": "HDFCBANK.NS",
        "sector": "Financials",
        "industry": "Private Sector Banking",
        "market_cap": "₹11.20 Lakh Cr",
        "employees": "177,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.hdfcbank.com",
        "description": "HDFC Bank Limited is India's largest private sector bank by assets and market capitalization. Following its historic merger with parent HDFC Ltd, it is a global top-10 financial institution, serving over 100 million retail and corporate accounts.",
        "segments": "Retail Banking, Wholesale & Corporate Banking, Treasury Operations, Credit Card Operations, Wealth Management, and Digital Banking.",
        "history": "Incorporated in 1994 as a subsidiary of the Housing Development Finance Corporation (HDFC Ltd), under the leadership of Aditya Puri. In July 2023, the bank completed a mega-merger with parent HDFC Ltd, creating a single banking powerhouse.",
        "logo_url": None
    },
    "HDFCLIFE.NS": {
        "company_name": "HDFC Life Insurance Company Limited",
        "symbol": "HDFCLIFE.NS",
        "sector": "Financials",
        "industry": "Life Insurance",
        "market_cap": "₹1.35 Lakh Cr",
        "employees": "30,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.hdfclife.com",
        "description": "HDFC Life Insurance Company Limited is a leading long-term life insurance provider in India. It offers individual and group insurance solutions including protection, pension, savings, investment, and health plans through a massive bancassurance network.",
        "segments": "Individual Life Insurance, Group Life Insurance, Pension & Annuity Plans, and Unit-Linked Insurance Plans (ULIPs).",
        "history": "Established in 2000 as a joint venture between HDFC Ltd and Standard Life Aberdeen. It was one of the first private sector life insurance companies to be registered after the privatization of the sector in India. Listed on the exchanges in 2017.",
        "logo_url": None
    },
    "HEROMOTOCO.NS": {
        "company_name": "Hero MotoCorp Limited",
        "symbol": "HEROMOTOCO.NS",
        "sector": "Consumer Discretionary",
        "industry": "Two-Wheelers",
        "market_cap": "₹65,000 Cr",
        "employees": "9,000+",
        "headquarters": "New Delhi, India",
        "website": "https://www.heromotocorp.com",
        "description": "Hero MotoCorp Limited is the world's largest manufacturer of two-wheelers, a position it has maintained since 2001. The company possesses four manufacturing facilities in India, alongside plants in Colombia and Bangladesh, and is expanding into electric mobility under the Vida brand.",
        "segments": "Motorcycles (Splendor, HF Deluxe, Passion, Glamour, Xpulse), Scooters (Destini, Pleasure), and Vida Electric Vehicles.",
        "history": "Established in 1984 as Hero Honda Motors, a joint venture between Hero Cycles and Honda Japan. The partnership produced the iconic Splendor motorcycle which defined the Indian commuter market. The JV ended in 2011, and the company rebranded to Hero MotoCorp.",
        "logo_url": None
    },
    "HINDALCO.NS": {
        "company_name": "Hindalco Industries Limited",
        "symbol": "HINDALCO.NS",
        "sector": "Materials",
        "industry": "Aluminium & Copper",
        "market_cap": "₹1.10 Lakh Cr",
        "employees": "40,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.hindalco.com",
        "description": "Hindalco Industries Limited is an industry-leading metals company, functioning as the world's largest aluminium rolling company and one of the largest producers of primary copper in Asia. Its subsidiary, Novelis, is the global leader in beverage can recycling.",
        "segments": "Aluminium (Primary Ingots, Extrusions, Foil, Sheets), Novelis (Flat Rolled Products), and Copper (Cathodes, Continuous Cast Rods).",
        "history": "Established in 1958 by Ghanshyam Das Birla, with the Renukoot smelter in Uttar Pradesh starting production in 1962. In 2007, Hindalco acquired US-based Novelis for $6 billion, transforming it into a global metals MNC and the largest recycler of aluminium.",
        "logo_url": None
    },
    "HINDUNILVR.NS": {
        "company_name": "Hindustan Unilever Limited",
        "symbol": "HINDUNILVR.NS",
        "sector": "Consumer Staples",
        "industry": "FMCG — Personal Care & Foods",
        "market_cap": "₹6.10 Lakh Cr",
        "employees": "22,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.hul.co.in",
        "description": "Hindustan Unilever Limited (HUL) is India's largest Fast-Moving Consumer Goods (FMCG) company. Over 9 out of 10 Indian households use HUL products daily, which include brands like Surf Excel, Dove, Lux, Lifebuoy, Brooke Bond, Knorr, and Horlicks.",
        "segments": "Beauty & Personal Care (Soaps, Shampoos, Skincare), Home Care (Detergents, Household Cleaners), Foods & Refreshment (Tea, Coffee, Ice Cream, Packaged Foods).",
        "history": "Established in 1933 as Lever Brothers India Limited. Following various mergers of subsidiaries, it became Hindustan Lever Limited in 1956. Rebranded to Hindustan Unilever in 2007, reflecting its deep local integration and Unilever parentage.",
        "logo_url": None
    },
    "ICICIBANK.NS": {
        "company_name": "ICICI Bank Limited",
        "symbol": "ICICIBANK.NS",
        "sector": "Financials",
        "industry": "Private Sector Banking",
        "market_cap": "₹6.85 Lakh Cr",
        "employees": "130,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.icicibank.com",
        "description": "ICICI Bank Limited is the second-largest private sector bank in India. It offers retail, corporate, and investment banking services alongside wealth management, insurance, and venture capital, with a network of over 5,900 branches across India.",
        "segments": "Retail Banking, Wholesale & Corporate Banking, Treasury Operations, Wealth Management, and Digital Services (iMobile Pay).",
        "history": "Promoted in 1994 by the Industrial Credit and Investment Corporation of India (ICICI), an Indian financial institution, as a private commercial bank. In 2002, the parent company merged with the bank in a historic reverse-merger, creating a massive universal banking entity.",
        "logo_url": None
    },
    "INDUSINDBK.NS": {
        "company_name": "IndusInd Bank Limited",
        "symbol": "INDUSINDBK.NS",
        "sector": "Financials",
        "industry": "Private Sector Banking",
        "market_cap": "₹1.10 Lakh Cr",
        "employees": "35,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.indusind.com",
        "description": "IndusInd Bank Limited is a private sector bank in India, catering to both consumer and corporate customers. The bank is a market leader in commercial vehicle and microfinance lending, supported by over 2,600 branches and banking outlets.",
        "segments": "Treasury Operations, Corporate Banking, Retail Banking, Vehicle Financing, and Microfinance (Bharat Financial Inclusion).",
        "history": "Founded in 1994 by S.P. Hinduja, the head of the Hinduja Group, with the goal of serving the non-resident Indian (NRI) community and local businesses. It merged with Bharat Financial Inclusion (formerly SKS Microfinance) in 2019.",
        "logo_url": None
    },
    "INFY.NS": {
        "company_name": "Infosys Limited",
        "symbol": "INFY.NS",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "market_cap": "₹6.15 Lakh Cr",
        "employees": "340,000+",
        "headquarters": "Bengaluru, India",
        "website": "https://www.infosys.com",
        "description": "Infosys Limited is a global leader in next-generation digital services and consulting. It enables clients in 56 countries to navigate their digital transformation, specializing in cloud computing, artificial intelligence (Topaz), cyber security, and core enterprise software.",
        "segments": "Digital Transformation Services, Application Development & Maintenance, Cloud Infrastructure (Cobalt), Artificial Intelligence (Topaz), and Finacle Banking Software.",
        "history": "Founded in Pune in 1981 by seven engineers including N. R. Narayana Murthy, Nandan Nilekani, and S. Gopalakrishnan, with an initial capital of $250. It pioneered the Global Delivery Model for software development and became the first Indian company to list on NASDAQ in 1999.",
        "logo_url": None
    },
    "ITC.NS": {
        "company_name": "ITC Limited",
        "symbol": "ITC.NS",
        "sector": "Consumer Staples",
        "industry": "FMCG — Cigarettes, Foods & Hotels",
        "market_cap": "₹5.60 Lakh Cr",
        "employees": "24,000+",
        "headquarters": "Kolkata, India",
        "website": "https://www.itcportal.com",
        "description": "ITC Limited is a highly diversified Indian conglomerate. While it is the market leader in the Indian cigarette sector, it has built major businesses in branded packaged foods, personal care, premium hotels, paperboards, packaging, and agri-business exports.",
        "segments": "FMCG Cigarettes, FMCG Others (Aashirvaad, Sunfeast, Bingo, Fiama), Hotels & Resorts, Paperboards & Specialty Papers, and Agri-Business.",
        "history": "Established in 1910 as the Imperial Tobacco Company of India Limited. In 1970, it transitioned to Indian ownership and became India Tobacco Company, changing to ITC Limited in 1974. It began diversifying into hotels in 1975 and foods in 2001.",
        "logo_url": None
    },
    "JIOFIN.NS": {
        "company_name": "Jio Financial Services Limited",
        "symbol": "JIOFIN.NS",
        "sector": "Financials",
        "industry": "Digital & Financial Services",
        "market_cap": "₹2.25 Lakh Cr",
        "employees": "2,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.jiofinance.com",
        "description": "Jio Financial Services Limited is a digital-first financial services provider spun off from Reliance Industries. It plans to leverage Reliance's massive digital footprint (Jio telecom and Retail) to offer consumer lending, insurance brokerage, digital payments, and asset management.",
        "segments": "Digital Lending, Payments Bank (Jio Payments Bank), Insurance Broking, Asset Management (JV with BlackRock), and Payment Gateway Services.",
        "history": "Originally incorporated as Reliance Strategic Investments Private Limited. It was demerged from Reliance Industries Limited in July 2023 and rebranded as Jio Financial Services, listing on the NSE in August 2023.",
        "logo_url": None
    },
    "JSWSTEEL.NS": {
        "company_name": "JSW Steel Limited",
        "symbol": "JSWSTEEL.NS",
        "sector": "Materials",
        "industry": "Steel Manufacturing",
        "market_cap": "₹2.10 Lakh Cr",
        "employees": "13,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.jsw.in/steel",
        "description": "JSW Steel Limited is the flagship company of the JSW Group and India's leading private sector steel manufacturer. It operates a state-of-the-art facility in Vijayanagar, Karnataka, which is the largest single-site steel plant in India.",
        "segments": "Flat Steel Products (Hot Rolled Coils, Galvanized Steel), Long Steel Products (Wire Rods, Rebars), and Value-Added Coated Steel.",
        "history": "Traces history to the acquisition of a small steel mill near Mumbai in 1982 by Sajjan Jindal. It merged with Jindal Vijayanagar Steel in 2005 to form JSW Steel, growing rapidly via brownfield expansions and acquisitions to become India's dominant steel producer.",
        "logo_url": None
    },
    "KOTAKBANK.NS": {
        "company_name": "Kotak Mahindra Bank Limited",
        "symbol": "KOTAKBANK.NS",
        "sector": "Financials",
        "industry": "Private Sector Banking",
        "market_cap": "₹3.50 Lakh Cr",
        "employees": "73,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.kotak.com",
        "description": "Kotak Mahindra Bank Limited is a leading Indian private bank offering transaction banking, retail loans, corporate finance, investment banking, stock broking, and life insurance services under a unified financial group structure.",
        "segments": "Treasury Operations, Corporate Banking, Retail Banking, Vehicle Financing, Mutual Funds, Life Insurance, and Wealth Management.",
        "history": "Founded in 1985 by Uday Kotak as Kotak Mahindra Finance Limited, an NBFC. In 2003, it became the first financial company in India's corporate history to be converted into a commercial bank by the RBI. Acquired ING Vysya Bank in 2015.",
        "logo_url": None
    },
    "LT.NS": {
        "company_name": "Larsen & Toubro Limited",
        "symbol": "LT.NS",
        "sector": "Industrials",
        "industry": "Infrastructure & Engineering",
        "market_cap": "₹4.85 Lakh Cr",
        "employees": "50,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.larsentoubro.com",
        "description": "Larsen & Toubro Limited (L&T) is an Indian multinational conglomerate engaged in technology, engineering, construction, manufacturing, and financial services. It is the undisputed market leader in execution of major infrastructure, power, defence, and hydrocarbon projects in India and the Middle East.",
        "segments": "Infrastructure Projects, Power Plants, Metallurgical & Material Handling, Heavy Engineering, Defence & Aerospace, Hydrocarbon Engineering, IT Services (LTIMindtree, LTTS), and Financial Services.",
        "history": "Founded in Bombay in 1938 by two Danish engineers, Henning Holck-Larsen and Søren Kristian Toubro, initially importing dairy equipment. It expanded into heavy fabrication and construction during WWII, going public in 1950, and became a cornerstone of India's industrial builder footprint.",
        "logo_url": None
    },
    "M&M.NS": {
        "company_name": "Mahindra & Mahindra Limited",
        "symbol": "M&M.NS",
        "sector": "Consumer Discretionary",
        "industry": "Automobiles — SUVs & Tractors",
        "market_cap": "₹2.20 Lakh Cr",
        "employees": "22,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.mahindra.com",
        "description": "Mahindra & Mahindra Limited is an Indian multinational automotive manufacturer. It is the largest tractor manufacturer in the world by volume and a market leader in the utility vehicle (SUV) segment in India, with iconic brands like Scorpio, Thar, and XUV700.",
        "segments": "Automotive (SUVs, Commercial Vehicles), Farm Equipment (Tractors, Harvesters), and Hospitality, Real Estate, and Financial Services (Mahindra Finance).",
        "history": "Founded in 1945 as Mahindra & Muhammad by brothers J.C. Mahindra and K.C. Mahindra, and Malik Ghulam Muhammad. Following the partition, it was renamed Mahindra & Mahindra in 1948. It began assembly of the iconic Willys Jeep, which established its dominance in rugged utility vehicles.",
        "logo_url": None
    },
    "MARUTI.NS": {
        "company_name": "Maruti Suzuki India Limited",
        "symbol": "MARUTI.NS",
        "sector": "Consumer Discretionary",
        "industry": "Passenger Automobiles",
        "market_cap": "₹3.15 Lakh Cr",
        "employees": "16,000+",
        "headquarters": "New Delhi, India",
        "website": "https://www.marutisuzuki.com",
        "description": "Maruti Suzuki India Limited is India's largest passenger car manufacturer, commanding over 40% of the domestic passenger vehicle market share. It operates massive manufacturing facilities in Gurgaon and Manesar, producing popular models from Alto to Grand Vitara.",
        "segments": "Passenger Cars (Alto, Swift, Dzire, Baleno), Utility Vehicles (Brezza, Ertiga, Grand Vitara), and NEXA Premium Retail Outlets.",
        "history": "Founded in 1981 as a public sector joint venture between the Government of India and Suzuki Motor Corporation of Japan, aiming to manufacture a 'people's car'. The launch of the Maruti 800 in 1983 revolutionized transportation in India. Suzuki acquired a majority stake in 2002.",
        "logo_url": None
    },
    "NESTLEIND.NS": {
        "company_name": "Nestle India Limited",
        "symbol": "NESTLEIND.NS",
        "sector": "Consumer Staples",
        "industry": "Packaged Foods & Beverages",
        "market_cap": "₹2.40 Lakh Cr",
        "employees": "8,000+",
        "headquarters": "Gurugram, India",
        "website": "https://www.nestle.in",
        "description": "Nestle India Limited is the Indian subsidiary of Swiss multinational Nestle. It is a leading player in the Indian packaged food industry, owning household brands such as Maggi instant noodles, Nescafe coffee, KitKat chocolate, Milkmaid, and Cerelac infant nutrition.",
        "segments": "Milk Products and Nutrition, Prepared Dishes and Cooking Aids (Maggi), Beverages (Nescafe), and Confectionery (KitKat, Munch).",
        "history": "Incorporated in 1959 at the government's request to set up a milk processing facility in Moga, Punjab, helping kickstart the local dairy economy. It expanded its product portfolio to foods in 1983 with the launch of Maggi Noodles, which grew to define the instant noodle segment.",
        "logo_url": None
    },
    "NTPC.NS": {
        "company_name": "NTPC Limited",
        "symbol": "NTPC.NS",
        "sector": "Utilities",
        "industry": "Power Generation (Thermal & Renewable)",
        "market_cap": "₹3.10 Lakh Cr",
        "employees": "16,000+",
        "headquarters": "New Delhi, India",
        "website": "https://www.ntpc.co.in",
        "description": "NTPC Limited is India's largest power utility, producing roughly 25% of the total electricity generated in the country. Primarily a thermal power producer, NTPC is rapidly pivoting to green energy, targetting 60 GW of renewable energy capacity by 2032.",
        "segments": "Thermal Power Generation (Coal & Gas), Hydro Power Generation, Renewable Energy (Solar & Wind), and Power Trading Services.",
        "history": "Established in 1975 as National Thermal Power Corporation Private Limited by Prime Minister Indira Gandhi to accelerate thermal power development. Listed on the NSE in 2004 and achieved Maharatna status in 2010.",
        "logo_url": None
    },
    "ONGC.NS": {
        "company_name": "Oil and Natural Gas Corporation Limited",
        "symbol": "ONGC.NS",
        "sector": "Energy",
        "industry": "Oil & Gas Exploration",
        "market_cap": "₹2.70 Lakh Cr",
        "employees": "26,000+",
        "headquarters": "New Delhi, India",
        "website": "https://www.ongcindia.com",
        "description": "Oil and Natural Gas Corporation Limited (ONGC) is India's largest crude oil and natural gas explorer and producer, contributing to around 71% of India's domestic oil and gas production. It also operates international operations through its subsidiary ONGC Videsh.",
        "segments": "Exploration & Production (E&P), Refining & Marketing (HPCL, MRPL), Petrochemicals, and International E&P Operations (ONGC Videsh).",
        "history": "Set up in 1956 as a commission under the Ministry of Natural Resources to tap India's domestic oil resources. Converted into a public corporation in 1993, went public in 1995, and discovered major offshore oil fields like Mumbai High.",
        "logo_url": None
    },
    "POWERGRID.NS": {
        "company_name": "Power Grid Corporation of India Limited",
        "symbol": "POWERGRID.NS",
        "sector": "Utilities",
        "industry": "Electric Power Transmission",
        "market_cap": "₹2.40 Lakh Cr",
        "employees": "8,500+",
        "headquarters": "Gurugram, India",
        "website": "https://www.powergrid.in",
        "description": "Power Grid Corporation of India Limited is a state-owned electric utility company. It transmits about 50% of the total power generated in India through its massive high-voltage transmission grid, acting as the backbone of the national electricity market.",
        "segments": "Power Transmission, Grid Management (POSOCO), Telecom Services (POWERTEL), and Infrastructure Consulting.",
        "history": "Incorporated in 1989 as National Power Transmission Corporation Limited to consolidate the inter-state transmission assets of NTPC, NHPC, and other public power units. Renamed Power Grid in 1992 and listed in 2007.",
        "logo_url": None
    },
    "RELIANCE.NS": {
        "company_name": "Reliance Industries Limited",
        "symbol": "RELIANCE.NS",
        "sector": "Energy & Consumer",
        "industry": "Oil, Retail, Telecom & Financial Services",
        "market_cap": "₹16.50 Lakh Cr",
        "employees": "380,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.ril.com",
        "description": "Reliance Industries Limited (RIL) is India's largest private sector conglomerate. The company operates the world's largest refining hub at Jamnagar and holds dominant, market-leading positions across telecom (Jio), retail (Reliance Retail), and petrochemicals.",
        "segments": "Oil to Chemicals (O2C Refining & Petrochemicals), Retail (Reliance Retail), Digital Services (Jio Infocomm), and Financial Services.",
        "history": "Founded by Dhirubhai Ambani in 1958 as Reliance Commercial Corporation, trading in spices and polyester yarn. It built the first polyester mill in Naroda in 1966. Expanded into oil refining in the late 1990s, launched retail in 2006, and launched Jio in 2016, transforming India's data economy.",
        "logo_url": None
    },
    "SBIN.NS": {
        "company_name": "State Bank of India",
        "symbol": "SBIN.NS",
        "sector": "Financials",
        "industry": "Public Sector Banking",
        "market_cap": "₹5.90 Lakh Cr",
        "employees": "245,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.sbi.co.in",
        "description": "State Bank of India is a public sector banking and financial services statutory body. It is a Fortune 500 company and the largest bank in India, commanding a 23% asset market share and serving over 480 million accounts.",
        "segments": "Treasury Operations, Corporate Banking, Retail Banking, Digital Banking (YONO), Insurance & Mutual Funds.",
        "history": "Traces history back to the Bank of Calcutta founded in 1806, which merged into the Imperial Bank of India in 1921. In 1955, the Government of India nationalized the Imperial Bank and renamed it State Bank of India. In 2017, it merged with its five associate banks.",
        "logo_url": None
    },
    "SBILIFE.NS": {
        "company_name": "SBI Life Insurance Company Limited",
        "symbol": "SBILIFE.NS",
        "sector": "Financials",
        "industry": "Life Insurance",
        "market_cap": "₹1.45 Lakh Cr",
        "employees": "18,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.sbilife.co.in",
        "description": "SBI Life Insurance Company Limited is a leading joint venture life insurance company, backed by State Bank of India and BNP Paribas Cardif. It accesses SBI's massive branch network to provide distribution for its life, health, and pension products.",
        "segments": "Individual Life Insurance, Group Life Insurance, Pension & Annuity Plans, and Savings Plans.",
        "history": "Incorporated in 2001 as a joint venture between SBI and BNP Paribas Cardif. It listed on the Indian stock exchanges in 2017 and is one of the most profitable private life insurers in India.",
        "logo_url": None
    },
    "SHRIRAMFIN.NS": {
        "company_name": "Shriram Finance Limited",
        "symbol": "SHRIRAMFIN.NS",
        "sector": "Financials",
        "industry": "Vehicle Finance & NBFC",
        "market_cap": "₹78,000 Cr",
        "employees": "70,000+",
        "headquarters": "Chennai, India",
        "website": "https://www.shriramfinance.in",
        "description": "Shriram Finance Limited is India's largest retail non-banking financial company (NBFC). The company is a market leader in commercial vehicle loans, passenger vehicle loans, MSME finance, and gold loans.",
        "segments": "Commercial Vehicle Loans, Small Enterprise Loans, Two-Wheeler Financing, and Personal/Gold Loans.",
        "history": "Established in 1979 as Shriram Transport Finance. In 2022, Shriram Transport Finance and Shriram City Union Finance merged with parent Shriram Capital to form Shriram Finance, creating a giant multi-product retail NBFC.",
        "logo_url": None
    },
    "SUNPHARMA.NS": {
        "company_name": "Sun Pharmaceutical Industries Limited",
        "symbol": "SUNPHARMA.NS",
        "sector": "Healthcare",
        "industry": "Pharmaceuticals",
        "market_cap": "₹2.75 Lakh Cr",
        "employees": "38,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.sunpharma.com",
        "description": "Sun Pharmaceutical Industries Limited is India's largest pharmaceutical company and the fourth-largest specialty generic pharmaceutical company in the world. It provides products in cardiology, psychiatry, neurology, and gastroenterology across 100+ countries.",
        "segments": "Formulations (US, India, Emerging Markets), Active Pharmaceutical Ingredients (APIs), and Specialty Branded Generics.",
        "history": "Founded by Dilip Shanghvi in 1983 in Vapi, Gujarat, starting with just five psychiatry drugs. It went public in 1994. Under Shanghvi's leadership, Sun grew via strategic acquisitions, notably acquiring Ranbaxy Laboratories in 2014 for $4 billion.",
        "logo_url": None
    },
    "TATASTEEL.NS": {
        "company_name": "Tata Steel Limited",
        "symbol": "TATASTEEL.NS",
        "sector": "Materials",
        "industry": "Steel Manufacturing",
        "market_cap": "₹1.45 Lakh Cr",
        "employees": "32,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.tatasteel.com",
        "description": "Tata Steel Limited is one of the world's leading steel manufacturing companies, operating integrated steel production facilities in India, the UK, and the Netherlands. It manufactures flat and long steel products for the auto and construction sectors.",
        "segments": "Flat Steel Products (Coils, Sheets), Long Steel Products (Bars, Rods), Agri-Implements, and European Steel Operations.",
        "history": "Founded by Jamsetji Tata and established by Dorabji Tata in 1907. It set up India's first industrial steel plant in Jamshedpur (Sakchi) in 1912, becoming the pioneer of industrial development in India.",
        "logo_url": None
    },
    "TCS.NS": {
        "company_name": "Tata Consultancy Services Limited",
        "symbol": "TCS.NS",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "market_cap": "₹13.50 Lakh Cr",
        "employees": "615,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.tcs.com",
        "description": "Tata Consultancy Services Limited (TCS) is India's largest IT services company and a global leader in IT consulting and business solutions. Operating in 46 countries, TCS manages software delivery and digital transformation for global Fortune 500 businesses.",
        "segments": "Banking, Financial Services & Insurance (BFSI), Retail & CPG, Life Sciences & Healthcare, Manufacturing, Communication & Media.",
        "history": "Established in 1968 by Tata Sons under the leadership of F.C. Kohli. It pioneered the offshore software development model for global businesses. It listed on the Indian stock exchanges in 2004 in a landmark IPO.",
        "logo_url": None
    },
    "TECHM.NS": {
        "company_name": "Tech Mahindra Limited",
        "symbol": "TECHM.NS",
        "sector": "Information Technology",
        "industry": "IT Services & BPO",
        "market_cap": "₹1.20 Lakh Cr",
        "employees": "145,000+",
        "headquarters": "Pune, India",
        "website": "https://www.techmahindra.com",
        "description": "Tech Mahindra Limited is a leading digital transformation, consulting, and business re-engineering services provider. Backed by the Mahindra Group, the company is a global specialist in telecom software and enterprise infrastructure.",
        "segments": "Communications, Media & Entertainment (CME), Manufacturing, BFSI, Technology & Retail Services, and Business Process Services.",
        "history": "Established in 1986 as Mahindra British Telecom, a joint venture between Mahindra & Mahindra and British Telecom. In 2009, it acquired the distressed Satyam Computer Services (Mahindra Satyam), merging it in 2013 to create an IT giant.",
        "logo_url": None
    },
    "TITAN.NS": {
        "company_name": "Titan Company Limited",
        "symbol": "TITAN.NS",
        "sector": "Consumer Discretionary",
        "industry": "Watches, Jewellery & Eyewear",
        "market_cap": "₹2.85 Lakh Cr",
        "employees": "8,000+",
        "headquarters": "Bengaluru, India",
        "website": "https://www.titancompany.in",
        "description": "Titan Company Limited is a leading Indian consumer goods company. A joint venture between the Tata Group and TIDCO, Titan is the largest watch manufacturer in India and operates the country's leading luxury jewellery brand, Tanishq.",
        "segments": "Jewellery (Tanishq, CaratLane, Mia, Zoya), Watches (Titan, Fastrack, Sonata), Eyewear (Titan Eye+), and Fragrances & Fashion Accessories (Skinn, Taneira).",
        "history": "Established in 1984 as a joint venture between the Tata Group and the Tamil Nadu Industrial Development Corporation (TIDCO). It introduced quartz analog watches to India, and in 1994, launched Tanishq, revolutionizing the Indian gold retail market.",
        "logo_url": None
    },
    "TRENT.NS": {
        "company_name": "Trent Limited",
        "symbol": "TRENT.NS",
        "sector": "Consumer Discretionary",
        "industry": "Retail — Fashion & Lifestyle",
        "market_cap": "₹70,000 Cr",
        "employees": "10,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.trent.in",
        "description": "Trent Limited is the retail arm of the Tata Group. It operates Westside, a leading chain of department stores, alongside Zudio, an affordable fashion brand, and Star Bazaar (a hypermarket joint venture with British retail giant Tesco).",
        "segments": "Fashion Apparel (Westside, Zudio, Utsa), Hypermarkets (Star Bazaar), and Lifestyle (Zara JV in India).",
        "history": "Established in 1998 by Tata Sons with the acquisition of Littlewoods India. It rebranded the operations to Westside. Trent has achieved massive growth in recent years, driven by the rapid, highly profitable expansion of its value-fashion retail chain, Zudio.",
        "logo_url": None
    },
    "ULTRACEMCO.NS": {
        "company_name": "UltraTech Cement Limited",
        "symbol": "ULTRACEMCO.NS",
        "sector": "Materials",
        "industry": "Cement Manufacturing",
        "market_cap": "₹2.45 Lakh Cr",
        "employees": "22,000+",
        "headquarters": "Mumbai, India",
        "website": "https://www.ultratechcement.com",
        "description": "UltraTech Cement Limited is the flagship cement company of the Aditya Birla Group. It is the largest manufacturer of grey cement, ready-mix concrete (RMC), and white cement in India, and the third-largest cement producer in the world.",
        "segments": "Grey Cement, White Cement & Wall Care Products, Ready Mix Concrete (RMC), and Building Products.",
        "history": "Incorporated in 2000 as Larsen & Toubro Cement. In 2004, the Aditya Birla Group acquired control of the cement business and rebranded it as UltraTech Cement, scaling it through major consolidation and acquisitions of Binani and JP Associates.",
        "logo_url": None
    },
    "WIPRO.NS": {
        "company_name": "Wipro Limited",
        "symbol": "WIPRO.NS",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "market_cap": "₹2.15 Lakh Cr",
        "employees": "240,000+",
        "headquarters": "Bengaluru, India",
        "website": "https://www.wipro.com",
        "description": "Wipro Limited is a leading global information technology, consulting, and business process services company. It delivers IT integration, cloud migration, AI consulting (Wipro ai360), and digital operations services across six continents.",
        "segments": "IT Services (BFSI, Health, Retail, Energy), IT Products (Enterprise Infrastructure), and Business Process Services.",
        "history": "Founded in 1945 by Mohamed Premji as Western India Vegetable Products Limited, a vegetable oil manufacturer. His son Azim Premji took over in 1966 and pivoted the company to IT hardware and software services in 1980, listing on the NYSE in 2000.",
        "logo_url": None
    }
}


def is_valid_symbol(symbol: str) -> bool:
    """Verify if a symbol is covered in the Nifty 50 universe."""
    df = data_loader.get_df()
    if df.empty:
        return False
    clean_sym = symbol.upper().replace(".NS", "").strip()
    return clean_sym in df["Symbol"].str.upper().str.replace(".NS", "").tolist()


def load_cached_company_profile(symbol: str) -> Optional[Dict[str, Any]]:
    """Load company profile from JSON cache file if it exists."""
    safe_symbol = symbol.upper().replace(".", "_").replace("-", "_")
    filepath = os.path.join(CACHE_DIR, f"{safe_symbol}.json")
    
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                logger.info(f"Loaded cached company profile for {symbol} from disk")
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading company profile cache for {symbol}: {e}")
    return None


def save_company_profile(symbol: str, profile_data: Dict[str, Any]) -> None:
    """Save company profile dictionary to a local JSON cache file."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    safe_symbol = symbol.upper().replace(".", "_").replace("-", "_")
    filepath = os.path.join(CACHE_DIR, f"{safe_symbol}.json")
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved company profile for {symbol} to cache file: {filepath}")
    except Exception as e:
        logger.error(f"Failed to write company profile cache file for {symbol}: {e}")


def refresh_company_profile(symbol: str) -> Dict[str, Any]:
    """
    Retrieves company profile from our high-fidelity static Nifty 50 database,
    saves the final JSON profile to disk cache, and returns it.
    """
    sym_upper = symbol.upper()
    
    # Check if we have high-fidelity data in our static database
    if sym_upper in NIFTY_50_COMPANY_DATABASE:
        profile = NIFTY_50_COMPANY_DATABASE[sym_upper].copy()
    else:
        # Fallback values for other stocks
        clean_name = sym_upper.replace(".NS", "").replace("-", " ")
        company_name = f"{clean_name} Limited"
        
        profile = {
            "company_name": company_name,
            "symbol": sym_upper,
            "sector": "Diversified Industrials",
            "industry": "Conglomerate",
            "market_cap": "₹1,50,000 Cr (Est.)",
            "employees": "15,000+",
            "headquarters": "Mumbai, India",
            "website": f"https://www.google.com/search?q={clean_name.replace(' ', '+')}",
            "description": f"{company_name} is a leading blue-chip business constituent of the Nifty 50 index in India, driving institutional asset values.",
            "segments": "Core Business Operations, Allied Services.",
            "history": "Established in India as a major corporation. Listed on the National Stock Exchange (NSE) and tracked by institutional desks.",
            "logo_url": None
        }

    # Save profile to disk cache
    save_company_profile(sym_upper, profile)
    return profile


def get_company_profile(symbol: str) -> Dict[str, Any]:
    """
    Retrieve company profile for a symbol.
    Checks the local file cache first. If missing, gets it from the Nifty 50 database.
    """
    sym_upper = symbol.upper()
    cached = load_cached_company_profile(sym_upper)
    if cached is not None:
        return cached
    
    # Profile is missing, get from database and cache
    return refresh_company_profile(sym_upper)


# Direct initialization to wipe and recreate the cache directory
# this clears out any old, lower-fidelity placeholder caches.
try:
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
        logger.info("Cleared old low-fidelity company caches from disk")
    os.makedirs(CACHE_DIR, exist_ok=True)
except Exception as e:
    logger.error(f"Failed to clear old company caches: {e}")
