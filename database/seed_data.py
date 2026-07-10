import random
import sqlite3
from sqlite3 import Connection
import uuid
from datetime import datetime, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "ksp_crime_platform.db"
RNG = random.Random(42)


DISTRICTS = [
    ("Bengaluru Urban", "Bengaluru", 12.9716, 77.5946),
    ("Mysuru", "Mysuru", 12.2958, 76.6394),
    ("Belagavi", "Belagavi", 15.8497, 74.4977),
    ("Mangaluru", "Mangaluru", 12.9141, 74.8560),
    ("Hubballi-Dharwad", "Hubballi", 15.3647, 75.1240),
    ("Kalaburagi", "Kalaburagi", 17.3297, 76.8343),
    ("Shivamogga", "Shivamogga", 13.9299, 75.5681),
    ("Tumakuru", "Tumakuru", 13.3379, 77.1173),
]

FIRST_NAMES = [
    "Ravi", "Suresh", "Asha", "Kiran", "Meena", "Naveen", "Deepa", "Arjun",
    "Priya", "Manjunath", "Lakshmi", "Rahul", "Anitha", "Iqbal", "Sunil",
    "Vijay", "Roopa", "Farhan", "Geetha", "Prakash",
]

LAST_NAMES = [
    "Kumar", "Naik", "Reddy", "Gowda", "Shetty", "Patil", "Khan", "Rao",
    "Hegde", "Poojary", "Nair", "Sharma", "Ali", "Das", "Murthy",
]


def new_id():
    return str(uuid.uuid4())


def get_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Exception as e:
        print(f"[SEED_DATA] Error connecting to the database: {e}")
        return None


def _date(days_from_start):
    return (datetime(2023, 1, 1) + timedelta(days=days_from_start)).date().isoformat()


def _timestamp(days_from_start, hour=None):
    hour = RNG.randint(0, 23) if hour is None else hour
    minute = RNG.randint(0, 59)
    return (datetime(2023, 1, 1, hour, minute) + timedelta(days=days_from_start)).isoformat(sep=" ")


def _weighted_2023_timestamp():
    month_weights = {
        1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1,
        7: 1, 8: 1, 9: 1, 10: 2, 11: 2, 12: 1,
    }
    month = RNG.choices(list(month_weights), weights=list(month_weights.values()), k=1)[0]
    day = RNG.randint(1, 28)
    hour = RNG.choices([8, 10, 14, 18, 20, 22], weights=[1, 1, 1, 3, 3, 1], k=1)[0]
    return datetime(2023, month, day, hour, RNG.randint(0, 59)).isoformat(sep=" ")


def _person_name(index):
    return FIRST_NAMES[index % len(FIRST_NAMES)], LAST_NAMES[(index * 3) % len(LAST_NAMES)]


def seed_cases(conn:Connection, count=500):
    cases = []
    for index in range(1, count + 1):
        case = {
            "case_id": new_id(),
            "case_number": f"KSP-CASE-2023-{index:04d}",
            "title": f"Crime intelligence case {index:04d}",
            "description": "Synthetic case record for crime intelligence prototype.",
            "priority": RNG.choice(["Low", "Medium", "High", "Critical"]),
            "status": RNG.choice(["Open", "Under Investigation", "Chargesheet Filed", "Closed"]),
            "created_at": _timestamp(RNG.randint(0, 330)),
            "updated_at": _timestamp(RNG.randint(331, 364)),
        }
        cases.append(case)

    conn.executemany(
        """
        INSERT OR IGNORE INTO "Case"
        (case_id, case_number, title, description, priority, status, created_at, updated_at)
        VALUES (:case_id, :case_number, :title, :description, :priority, :status, :created_at, :updated_at)
        """,
        cases,
    )
    return cases


def seed_police_stations(conn:Connection):
    stations = []
    station_index = 1
    for district, city, latitude, longitude in DISTRICTS:
        for suffix in ["Central", "North", "South"]:
            station = {
                "station_id": new_id(),
                "station_name": f"{city} {suffix} Police Station",
                "district": district,
                "city": city,
                "address": f"{suffix} Division, {city}, Karnataka",
                "latitude": latitude + RNG.uniform(-0.04, 0.04),
                "longitude": longitude + RNG.uniform(-0.04, 0.04),
            }
            stations.append(station)
            station_index += 1

    conn.executemany(
        """
        INSERT OR IGNORE INTO PoliceStation
        (station_id, station_name, district, city, address, latitude, longitude)
        VALUES (:station_id, :station_name, :district, :city, :address, :latitude, :longitude)
        """,
        stations,
    )
    return stations


def seed_locations(conn:Connection):
    locations = []
    for district, city, latitude, longitude in DISTRICTS:
        for index in range(1, 16):
            locations.append(
                {
                    "location_id": new_id(),
                    "location_name": f"{city} Zone {index}",
                    "address": f"Ward {index}, {city}, Karnataka",
                    "district": district,
                    "city": city,
                    "state": "Karnataka",
                    "postal_code": f"56{RNG.randint(1000, 9999)}",
                    "latitude": latitude + RNG.uniform(-0.08, 0.08),
                    "longitude": longitude + RNG.uniform(-0.08, 0.08),
                }
            )

    conn.executemany(
        """
        INSERT OR IGNORE INTO Location
        (location_id, location_name, address, district, city, state, postal_code, latitude, longitude)
        VALUES (:location_id, :location_name, :address, :district, :city, :state, :postal_code, :latitude, :longitude)
        """,
        locations,
    )
    return locations


def seed_crime_types(conn:Connection):
    crime_types = [
        ("Chain Snatching", "Property Crime", 6),
        ("Vehicle Theft", "Property Crime", 5),
        ("Burglary", "Property Crime", 6),
        ("Robbery", "Violent Crime", 8),
        ("Assault", "Violent Crime", 7),
        ("Cyber Fraud", "Economic Crime", 5),
        ("Bank Fraud", "Economic Crime", 7),
        ("Extortion", "Organized Crime", 8),
        ("Drug Trafficking", "Organized Crime", 9),
        ("Kidnapping", "Violent Crime", 9),
    ]
    rows = [
        {
            "crime_type_id": new_id(),
            "crime_name": name,
            "category": category,
            "default_severity": severity,
        }
        for name, category, severity in crime_types
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO CrimeType
        (crime_type_id, crime_name, category, default_severity)
        VALUES (:crime_type_id, :crime_name, :category, :default_severity)
        """,
        rows,
    )
    return rows


def seed_modus_operandi(conn:Connection):
    modus = [
        ("Distract-and-snatch", "Two-person team distracts victim and snatches valuables."),
        ("Forced entry", "Entry by breaking lock or rear door after surveillance."),
        ("Phishing call", "Victim deceived through phone call or online payment link."),
        ("Gang attack", "Multiple accused coordinate intimidation or assault."),
        ("Vehicle lift-and-strip", "Vehicle stolen and dismantled for parts."),
    ]
    rows = [{"mo_id": new_id(), "mo_name": name, "description": description} for name, description in modus]
    conn.executemany(
        """
        INSERT OR IGNORE INTO ModusOperandi
        (mo_id, mo_name, description)
        VALUES (:mo_id, :mo_name, :description)
        """,
        rows,
    )
    return rows


def seed_persons(conn:Connection, count=200):
    persons = []
    for index in range(count):
        first_name, last_name = _person_name(index)
        birth_year = RNG.randint(1965, 2004)
        persons.append(
            {
                "person_id": new_id(),
                "first_name": first_name,
                "last_name": last_name,
                "gender": RNG.choice(["Male", "Female"]),
                "date_of_birth": f"{birth_year}-{RNG.randint(1, 12):02d}-{RNG.randint(1, 28):02d}",
                "occupation": RNG.choice(["Daily wage", "Driver", "Student", "Shop owner", "Unemployed", "Technician"]),
                "education_level": RNG.choice(["Primary", "Secondary", "PUC", "Graduate", "Unknown"]),
                "income_group": RNG.choice(["Low", "Lower Middle", "Middle", "Upper Middle"]),
                "nationality": "Indian",
                "created_at": _timestamp(RNG.randint(0, 364)),
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO Person
        (person_id, first_name, last_name, gender, date_of_birth, occupation, education_level,
         income_group, nationality, created_at)
        VALUES (:person_id, :first_name, :last_name, :gender, :date_of_birth, :occupation,
                :education_level, :income_group, :nationality, :created_at)
        """,
        persons,
    )
    return {
        "all": persons,
        "repeat_offenders": persons[:5],
        "accused_pool": persons[:80],
        "victim_pool": persons[80:180],
        "witness_pool": persons[120:],
    }


def seed_officers(conn:Connection, police_stations, count=24):
    officers = []
    ranks = ["Sub Inspector", "Inspector", "Deputy Superintendent", "Assistant Commissioner"]
    for index in range(count):
        first_name, last_name = _person_name(index + 50)
        station = police_stations[index % len(police_stations)]
        officers.append(
            {
                "officer_id": new_id(),
                "name": f"{first_name} {last_name}",
                "badge_number": f"KSP{index + 1:05d}",
                "rank": RNG.choice(ranks),
                "station_id": station["station_id"],
                "years_of_service": RNG.randint(2, 28),
                "specialization": RNG.choice(["Property Crime", "Cyber Crime", "Organized Crime", "Financial Crime"]),
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO Officer
        (officer_id, name, badge_number, rank, station_id, years_of_service, specialization)
        VALUES (:officer_id, :name, :badge_number, :rank, :station_id, :years_of_service, :specialization)
        """,
        officers,
    )
    return officers


def seed_evidence(conn:Connection, count=120):
    rows = []
    for index in range(1, count + 1):
        evidence_type = RNG.choice(["CCTV Footage", "Mobile Phone", "Vehicle", "Document", "Bank Record", "Witness Statement"])
        rows.append(
            {
                "evidence_id": new_id(),
                "evidence_type": evidence_type,
                "description": f"{evidence_type} collected for synthetic case {index}.",
                "collection_date": _date(RNG.randint(0, 364)),
                "forensic_status": RNG.choice(["Pending", "Submitted", "Analyzed", "Not Required"]),
                "storage_location": f"Evidence Room Rack {RNG.randint(1, 30)}",
                "chain_of_custody": "Collected by investigating officer and logged in station records.",
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO Evidence
        (evidence_id, evidence_type, description, collection_date, forensic_status, storage_location, chain_of_custody)
        VALUES (:evidence_id, :evidence_type, :description, :collection_date, :forensic_status,
                :storage_location, :chain_of_custody)
        """,
        rows,
    )
    return rows


def seed_vehicles(conn:Connection, count=80):
    rows = []
    for index in range(1, count + 1):
        rows.append(
            {
                "vehicle_id": new_id(),
                "registration_number": f"KA{RNG.randint(1, 70):02d}M{index:04d}",
                "vehicle_type": RNG.choice(["Motorcycle", "Scooter", "Car", "Auto Rickshaw", "Van"]),
                "manufacturer": RNG.choice(["Honda", "TVS", "Bajaj", "Hero", "Maruti", "Hyundai"]),
                "model": RNG.choice(["Activa", "Pulsar", "Splendor", "Swift", "i20", "Apache"]),
                "color": RNG.choice(["Black", "White", "Red", "Blue", "Silver"]),
                "manufacture_year": RNG.randint(2012, 2023),
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO Vehicle
        (vehicle_id, registration_number, vehicle_type, manufacturer, model, color, manufacture_year)
        VALUES (:vehicle_id, :registration_number, :vehicle_type, :manufacturer, :model, :color, :manufacture_year)
        """,
        rows,
    )
    return rows


def seed_phones(conn:Connection, count=180):
    rows = []
    for index in range(1, count + 1):
        rows.append(
            {
                "phone_id": new_id(),
                "phone_number": f"+91{RNG.randint(7000000000, 9999999999)}",
                "imei": f"{RNG.randint(100000000000000, 999999999999999)}",
                "network_provider": RNG.choice(["Jio", "Airtel", "Vi", "BSNL"]),
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO Phone
        (phone_id, phone_number, imei, network_provider)
        VALUES (:phone_id, :phone_number, :imei, :network_provider)
        """,
        rows,
    )
    return rows


def seed_bank_accounts(conn:Connection, count=80):
    rows = []
    for index in range(1, count + 1):
        rows.append(
            {
                "account_id": new_id(),
                "bank_name": RNG.choice(["SBI", "Canara Bank", "Karnataka Bank", "HDFC Bank", "ICICI Bank"]),
                "account_number": f"{RNG.randint(10**11, 10**12 - 1)}",
                "ifsc": f"KARB{RNG.randint(1000000, 9999999)}",
                "account_type": RNG.choice(["Savings", "Current"]),
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO BankAccount
        (account_id, bank_name, account_number, ifsc, account_type)
        VALUES (:account_id, :bank_name, :account_number, :ifsc, :account_type)
        """,
        rows,
    )
    return rows


def seed_organizations(conn:Connection):
    rows = [
        {
            "organization_id": new_id(),
            "organization_name": "Bengaluru North Gang",
            "organization_type": "Criminal Gang",
            "description": "Synthetic organized group involved in chain snatching and vehicle theft.",
        },
        {
            "organization_id": new_id(),
            "organization_name": "Mysuru Fraud Ring",
            "organization_type": "Financial Crime Network",
            "description": "Synthetic group linked to phishing and bank fraud cases.",
        },
    ]

    conn.executemany(
        """
        INSERT OR IGNORE INTO Organization
        (organization_id, organization_name, organization_type, description)
        VALUES (:organization_id, :organization_name, :organization_type, :description)
        """,
        rows,
    )
    return rows


def seed_firs(conn:Connection, cases, police_stations, count=500):
    firs = []
    for index, case in enumerate(cases[:count], start=1):
        station = RNG.choice(police_stations)
        firs.append(
            {
                "fir_id": new_id(),
                "case_id": case["case_id"],
                "fir_number": f"KSP/2023/{index:04d}",
                "police_station_id": station["station_id"],
                "filing_date": _date(RNG.randint(0, 364)),
                "complainant_name": f"{RNG.choice(FIRST_NAMES)} {RNG.choice(LAST_NAMES)}",
                "description": "FIR generated for synthetic crime intelligence dataset.",
                "status": RNG.choice(["Registered", "Under Investigation", "Chargesheet Filed", "Closed"]),
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO FIR
        (fir_id, case_id, fir_number, police_station_id, filing_date, complainant_name, description, status)
        VALUES (:fir_id, :case_id, :fir_number, :police_station_id, :filing_date,
                :complainant_name, :description, :status)
        """,
        firs,
    )
    return firs


def seed_crime_incidents(conn:Connection, firs, locations, crime_types, modus_operandi, count=520):
    incidents = []
    bengaluru_locations = [row for row in locations if row["district"] == "Bengaluru Urban"]
    other_locations = [row for row in locations if row["district"] != "Bengaluru Urban"]
    crime_by_name = {row["crime_name"]: row for row in crime_types}
    mo_by_name = {row["mo_name"]: row for row in modus_operandi}

    for index in range(count):
        fir = firs[index % len(firs)]
        location = RNG.choice(bengaluru_locations if RNG.random() < 0.40 else other_locations)
        if RNG.random() < 0.18:
            crime_type = crime_by_name["Chain Snatching"]
            mo = mo_by_name["Distract-and-snatch"]
        elif RNG.random() < 0.16:
            crime_type = crime_by_name["Vehicle Theft"]
            mo = mo_by_name["Vehicle lift-and-strip"]
        else:
            crime_type = RNG.choice(crime_types)
            mo = RNG.choice(modus_operandi)
            if mo["mo_name"] == "Distract-and-snatch":
                crime_type = crime_by_name["Chain Snatching"]

        incidents.append(
            {
                "incident_id": new_id(),
                "fir_id": fir["fir_id"],
                "crime_type_id": crime_type["crime_type_id"],
                "crime_name": crime_type["crime_name"],
                "mo_id": mo["mo_id"],
                "mo_name": mo["mo_name"],
                "location_id": location["location_id"],
                "district": location["district"],
                "crime_datetime": _weighted_2023_timestamp(),
                "weapon_used": RNG.choice(["None", "Knife", "Blunt object", "Unknown"]),
                "severity": min(10, max(1, crime_type["default_severity"] + RNG.randint(-1, 2))),
                "status": RNG.choice(["Reported", "Under Investigation", "Accused Arrested", "Closed"]),
                "description": f"{crime_type['crime_name']} using {mo['mo_name']} reported in {location['district']}.",
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO CrimeIncident
        (incident_id, fir_id, crime_type_id, mo_id, location_id, crime_datetime,
         weapon_used, severity, status, description)
        VALUES (:incident_id, :fir_id, :crime_type_id, :mo_id, :location_id, :crime_datetime,
                :weapon_used, :severity, :status, :description)
        """,
        incidents,
    )
    return incidents


def seed_investigations(conn:Connection, incidents, officers):
    rows = []
    for incident in incidents:
        officer = RNG.choice(officers)
        rows.append(
            {
                "investigation_id": new_id(),
                "incident_id": incident["incident_id"],
                "officer_id": officer["officer_id"],
                "status": RNG.choice(["Open", "Field Inquiry", "Evidence Review", "Chargesheet Filed", "Closed"]),
                "priority": "High" if incident["severity"] >= 8 else RNG.choice(["Low", "Medium", "High"]),
                "assigned_date": incident["crime_datetime"][:10],
                "closed_date": None if RNG.random() < 0.65 else _date(RNG.randint(200, 364)),
                "next_action": RNG.choice(["Interview witnesses", "Review CCTV", "Trace financial links", "Locate accused"]),
                "remarks": "Synthetic investigation record.",
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO Investigation
        (investigation_id, incident_id, officer_id, status, priority, assigned_date,
         closed_date, next_action, remarks)
        VALUES (:investigation_id, :incident_id, :officer_id, :status, :priority,
                :assigned_date, :closed_date, :next_action, :remarks)
        """,
        rows,
    )
    return rows


def seed_financial_transactions(conn:Connection, accounts, gang_account_ids=None, count=30):
    gang_account_ids = gang_account_ids or [account["account_id"] for account in accounts[:5]]
    rows = []
    for index in range(count):
        if index < 12 and len(gang_account_ids) >= 2:
            from_account_id, to_account_id = RNG.sample(gang_account_ids, 2)
        else:
            from_account_id, to_account_id = [account["account_id"] for account in RNG.sample(accounts, 2)]
        rows.append(
            {
                "transaction_id": new_id(),
                "from_account_id": from_account_id,
                "to_account_id": to_account_id,
                "amount": round(RNG.uniform(1500, 125000), 2),
                "transaction_date": _timestamp(RNG.randint(0, 364)),
                "transaction_type": RNG.choice(["UPI", "IMPS", "NEFT", "Cash Deposit"]),
                "remarks": RNG.choice(["goods", "loan repayment", "advance", "personal transfer"]),
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO FinancialTransaction
        (transaction_id, from_account_id, to_account_id, amount, transaction_date, transaction_type, remarks)
        VALUES (:transaction_id, :from_account_id, :to_account_id, :amount,
                :transaction_date, :transaction_type, :remarks)
        """,
        rows,
    )
    return rows


def seed_timeline_events(conn:Connection, incidents, officers):
    rows = []
    for incident in incidents:
        officer = RNG.choice(officers)
        rows.append(
            {
                "event_id": new_id(),
                "incident_id": incident["incident_id"],
                "officer_id": officer["officer_id"],
                "event_time": incident["crime_datetime"],
                "event_type": "FIR Registered",
                "description": "FIR registered and incident entered into investigation workflow.",
            }
        )
        if incident["severity"] >= 7:
            rows.append(
                {
                    "event_id": new_id(),
                    "incident_id": incident["incident_id"],
                    "officer_id": officer["officer_id"],
                    "event_time": _timestamp(RNG.randint(1, 364)),
                    "event_type": RNG.choice(["Evidence Collected", "Accused Arrested", "Witness Examined"]),
                    "description": "Follow-up investigation event for high-severity case.",
                }
            )

    conn.executemany(
        """
        INSERT OR IGNORE INTO TimelineEvent
        (event_id, incident_id, officer_id, event_time, event_type, description)
        VALUES (:event_id, :incident_id, :officer_id, :event_time, :event_type, :description)
        """,
        rows,
    )
    return rows


def seed_conversations(conn:Connection):
    rows = [
        {"conversation_id": new_id(), "user_id": "demo_investigator", "started_at": _timestamp(350)},
        {"conversation_id": new_id(), "user_id": "demo_analyst", "started_at": _timestamp(351)},
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO Conversation
        (conversation_id, user_id, started_at)
        VALUES (:conversation_id, :user_id, :started_at)
        """,
        rows,
    )
    return rows


def seed_messages(conn:Connection, conversations):
    prompts = [
        ("user", "Show all FIRs registered at Bengaluru Urban in October 2023"),
        ("assistant", "Found matching FIR records. Use the SQL explainability panel for the query."),
        ("user", "Show the criminal network for Ravi Kumar"),
        ("assistant", "Network graph prepared with co-accused, organization, and location links."),
    ]
    rows = []
    for index, (sender, content) in enumerate(prompts):
        conversation = conversations[index // 2]
        rows.append(
            {
                "message_id": new_id(),
                "conversation_id": conversation["conversation_id"],
                "sender": sender,
                "content": content,
                "created_at": _timestamp(352 + index),
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO Message
        (message_id, conversation_id, sender, content, created_at)
        VALUES (:message_id, :conversation_id, :sender, :content, :created_at)
        """,
        rows,
    )
    return rows


def seed_crime_participants(conn:Connection, incidents, person_groups):
    repeat_offenders = person_groups["repeat_offenders"]
    accused_pool = person_groups["accused_pool"]
    victim_pool = person_groups["victim_pool"]
    witness_pool = person_groups["witness_pool"]
    rows = []

    for index, incident in enumerate(incidents):
        if index < 60:
            accused = [repeat_offenders[index % len(repeat_offenders)]]
            if incident["mo_name"] == "Gang attack" or incident["crime_name"] in ["Chain Snatching", "Vehicle Theft"]:
                accused.append(repeat_offenders[(index + 1) % len(repeat_offenders)])
        elif RNG.random() < 0.20:
            accused = [RNG.choice(repeat_offenders), RNG.choice(accused_pool)]
        else:
            accused = RNG.sample(accused_pool, RNG.randint(1, 3))

        victim = RNG.choice(victim_pool)
        witness = RNG.choice(witness_pool)

        rows.append(
            {
                "participant_id": new_id(),
                "incident_id": incident["incident_id"],
                "person_id": victim["person_id"],
                "role": "Victim",
                "injury_status": RNG.choice(["None", "Minor", "Serious"]),
                "arrest_status": None,
                "remarks": "Victim recorded in synthetic FIR.",
            }
        )

        for person in accused:
            rows.append(
                {
                    "participant_id": new_id(),
                    "incident_id": incident["incident_id"],
                    "person_id": person["person_id"],
                    "role": "Accused",
                    "injury_status": None,
                    "arrest_status": RNG.choice(["Not Arrested", "Arrested", "Released on Bail"]),
                    "remarks": "Accused linked to incident.",
                }
            )

        if RNG.random() < 0.45:
            rows.append(
                {
                    "participant_id": new_id(),
                    "incident_id": incident["incident_id"],
                    "person_id": witness["person_id"],
                    "role": "Witness",
                    "injury_status": "None",
                    "arrest_status": None,
                    "remarks": "Witness statement available.",
                }
            )

    conn.executemany(
        """
        INSERT OR IGNORE INTO CrimeParticipant
        (participant_id, incident_id, person_id, role, injury_status, arrest_status, remarks)
        VALUES (:participant_id, :incident_id, :person_id, :role, :injury_status, :arrest_status, :remarks)
        """,
        rows,
    )
    return rows


def seed_person_addresses(conn:Connection, persons, locations):
    rows = []
    for person in persons:
        location = RNG.choice(locations)
        rows.append(
            {
                "person_address_id": new_id(),
                "person_id": person["person_id"],
                "location_id": location["location_id"],
                "address_type": RNG.choice(["Permanent", "Current"]),
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO PersonAddress
        (person_address_id, person_id, location_id, address_type)
        VALUES (:person_address_id, :person_id, :location_id, :address_type)
        """,
        rows,
    )
    return rows


def seed_person_vehicles(conn:Connection, persons, vehicles, repeat_offender_ids=None):
    repeat_offender_ids = repeat_offender_ids or [person["person_id"] for person in persons[:5]]
    rows = []
    for index, vehicle in enumerate(vehicles):
        person_id = repeat_offender_ids[index] if index < len(repeat_offender_ids) else RNG.choice(persons)["person_id"]
        rows.append(
            {
                "person_vehicle_id": new_id(),
                "person_id": person_id,
                "vehicle_id": vehicle["vehicle_id"],
                "ownership_type": RNG.choice(["Owner", "Rider", "Borrowed", "Suspected Use"]),
                "registered_from": _date(RNG.randint(0, 200)),
                "registered_to": None,
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO PersonVehicle
        (person_vehicle_id, person_id, vehicle_id, ownership_type, registered_from, registered_to)
        VALUES (:person_vehicle_id, :person_id, :vehicle_id, :ownership_type, :registered_from, :registered_to)
        """,
        rows,
    )
    return rows


def seed_person_phones(conn:Connection, persons, phones, repeat_offender_ids=None):
    repeat_offender_ids = repeat_offender_ids or [person["person_id"] for person in persons[:5]]
    rows = []
    for index, phone in enumerate(phones):
        person_id = repeat_offender_ids[index] if index < len(repeat_offender_ids) else RNG.choice(persons)["person_id"]
        rows.append(
            {
                "person_phone_id": new_id(),
                "person_id": person_id,
                "phone_id": phone["phone_id"],
                "start_date": _date(RNG.randint(0, 220)),
                "end_date": None if index < len(repeat_offender_ids) or RNG.random() < 0.80 else _date(RNG.randint(221, 364)),
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO PersonPhone
        (person_phone_id, person_id, phone_id, start_date, end_date)
        VALUES (:person_phone_id, :person_id, :phone_id, :start_date, :end_date)
        """,
        rows,
    )
    return rows


def seed_person_bank_accounts(conn:Connection, persons, accounts, repeat_offender_ids=None):
    repeat_offender_ids = repeat_offender_ids or [person["person_id"] for person in persons[:5]]
    rows = []
    gang_account_ids = []
    for index, account in enumerate(accounts):
        person_id = repeat_offender_ids[index] if index < len(repeat_offender_ids) else RNG.choice(persons)["person_id"]
        if index < len(repeat_offender_ids):
            gang_account_ids.append(account["account_id"])
        rows.append(
            {
                "person_bank_id": new_id(),
                "person_id": person_id,
                "account_id": account["account_id"],
                "relation_type": RNG.choice(["Primary Holder", "Joint Holder", "Suspected Beneficiary"]),
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO PersonBankAccount
        (person_bank_id, person_id, account_id, relation_type)
        VALUES (:person_bank_id, :person_id, :account_id, :relation_type)
        """,
        rows,
    )
    return {"rows": rows, "gang_account_ids": gang_account_ids}


def seed_person_organizations(conn:Connection, organizations, repeat_offender_ids):
    gang = next(row for row in organizations if row["organization_name"] == "Bengaluru North Gang")
    rows = []
    for index, person_id in enumerate(repeat_offender_ids):
        rows.append(
            {
                "person_org_id": new_id(),
                "person_id": person_id,
                "organization_id": gang["organization_id"],
                "role": "Leader" if index == 0 else "Member",
                "joined_date": _date(RNG.randint(0, 120)),
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO PersonOrganization
        (person_org_id, person_id, organization_id, role, joined_date)
        VALUES (:person_org_id, :person_id, :organization_id, :role, :joined_date)
        """,
        rows,
    )
    return rows


def seed_crime_evidence(conn:Connection, incidents, evidence):
    rows = []
    for index, item in enumerate(evidence):
        incident = incidents[index % len(incidents)]
        rows.append(
            {
                "crime_evidence_id": new_id(),
                "incident_id": incident["incident_id"],
                "evidence_id": item["evidence_id"],
            }
        )

    conn.executemany(
        """
        INSERT OR IGNORE INTO CrimeEvidence
        (crime_evidence_id, incident_id, evidence_id)
        VALUES (:crime_evidence_id, :incident_id, :evidence_id)
        """,
        rows,
    )
    return rows



# seed everything into the database
def seed_all():
    try:
        conn = get_connection()
        if conn is None:
            print("[SEED_DATA] Database connection failed. Aborting seeding process.")
            return 
        
        # seed each table in order, capturing returned data for relationships
        
        # 1. Seed Cases
        print(f"[SEED_DATA] Seeding Cases...")
        cases = seed_cases(conn=conn)
        
        # 2. Seed Police Stations
        print(f"[SEED_DATA] Seeding Police Stations...")
        police_stations = seed_police_stations(conn=conn)
        
        # 3. Seed Locations
        print(f"[SEED_DATA] Seeding Locations...")
        locations = seed_locations(conn=conn)
        
        # 4. Seed Crime Types
        print(f"[SEED_DATA] Seeding Crime Types...")
        crime_types = seed_crime_types(conn=conn)
        
        # 5. Seed Modus Operandi
        print(f"[SEED_DATA] Seeding Modus Operandi...")
        modus_operandi = seed_modus_operandi(conn=conn)
        
        # 6. Seed Persons
        print(f"[SEED_DATA] Seeding Persons...")
        person_groups = seed_persons(conn=conn)
        
        # 7. Seed Officers
        print(f"[SEED_DATA] Seeding Officers...")
        officers = seed_officers(conn=conn,police_stations=police_stations)
        
        # 8. Seed Evidence
        print(f"[SEED_DATA] Seeding Evidence...")
        evidence = seed_evidence(conn=conn)
        
        # 9. Seed Vehicles
        print(f"[SEED_DATA] Seeding Vehicles...")
        vehicles = seed_vehicles(conn=conn)
        
        # 10. Seed Phones
        print(f"[SEED_DATA] Seeding Phones...")
        phones = seed_phones(conn=conn)
        
        # 11. Seed Bank Accounts
        print(f"[SEED_DATA] Seeding Bank Accounts...")
        bank_accounts = seed_bank_accounts(conn=conn)
        
        # 12. Seed Organizations
        print(f"[SEED_DATA] Seeding Organizations...")
        organizations = seed_organizations(conn=conn)
        
        # 13. Seed FIRs
        print(f"[SEED_DATA] Seeding FIRs...")
        firs = seed_firs(conn=conn,cases=cases,police_stations=police_stations)
        
        # 14. Seed Crime Incidents
        print(f"[SEED_DATA] Seeding Crime Incidents...")
        incidents = seed_crime_incidents(conn=conn,firs=firs,locations=locations,crime_types=crime_types,modus_operandi=modus_operandi)
        
        # 15. Seed Investigations
        print(f"[SEED_DATA] Seeding Investigations...")
        investigations = seed_investigations(conn=conn,incidents=incidents,officers=officers)
        
        # 16. Seed Financial Transactions
        print(f"[SEED_DATA] Seeding Financial Transactions...")
        financial_transactions = seed_financial_transactions(conn=conn,accounts=bank_accounts)
        
        # 17. Seed Timeline Events
        print(f"[SEED_DATA] Seeding Timeline Events...")
        timeline_events = seed_timeline_events(conn=conn,incidents=incidents,officers=officers)
        
        # 18. Seed Conversations
        print(f"[SEED_DATA] Seeding Conversations...")
        conversations = seed_conversations(conn=conn)
        
        # 19. Seed Messages
        print(f"[SEED_DATA] Seeding Messages...")
        messages = seed_messages(conn=conn,conversations=conversations)
        
        # 20. Seed Crime Participants
        print(f"[SEED_DATA] Seeding Crime Participants...")
        crime_participants = seed_crime_participants(conn=conn,incidents=incidents,person_groups=person_groups)
        
        # 21. Seed Person Addresses
        print(f"[SEED_DATA] Seeding Person Addresses...")
        person_addresses = seed_person_addresses(conn=conn,persons=person_groups["all"],locations=locations)
        
        # 22. Seed Person Vehicles
        print(f"[SEED_DATA] Seeding Person Vehicles...")
        person_vehicles = seed_person_vehicles(conn=conn,persons=person_groups["all"],vehicles=vehicles)
        
        # 23. Seed Person Phones
        print(f"[SEED_DATA] Seeding Person Phones...")
        person_phones = seed_person_phones(conn=conn,persons=person_groups["all"],phones=phones)
        
        # 24. Seed Person Bank Accounts
        print(f"[SEED_DATA] Seeding Person Bank Accounts...")
        person_bank_accounts_info = seed_person_bank_accounts(conn=conn,persons=person_groups["all"],accounts=bank_accounts)
        gang_account_ids = person_bank_accounts_info["gang_account_ids"]
        
        # 25. Seed Person Organizations
        print(f"[SEED_DATA] Seeding Person Organizations...")
        person_organizations = seed_person_organizations(conn=conn,organizations=organizations,repeat_offender_ids=[person["person_id"] for person in person_groups["repeat_offenders"]])
        
        # 26. Seed Crime Evidence
        print(f"[SEED_DATA] Seeding Crime Evidence...")
        crime_evidence = seed_crime_evidence(conn=conn,incidents=incidents,evidence=evidence)
        
        # commit all the changes
        conn.commit()
        conn.close()
        
        print(f"[SEED_DATA] Seeding completed successfully.")
        
    except Exception as e:
        print(f"[SEED_DATA] Error during seeding: {e}")
        if conn:
            conn.rollback()
            conn.close()
            
            
# test query to verify data insertion
def test_query():
    conn = get_connection()
    cursor = conn.cursor()
    
    # firs
    cursor.execute("SELECT * FROM FIR LIMIT 5;")
    firs = cursor.fetchall()
    print("Sample FIRs:")
    for fir in firs:
        print(f"{fir['fir_number']} - {fir['description']} - {fir['status']} - {fir['complainant_name']}")
        
    cursor.execute("SELECT COUNT(*) FROM FIR;")
    fir_count = cursor.fetchone()
    print(f"Total FIRs: {fir_count[0]}")
    
    
    # crime incidents
    cursor.execute("SELECT * FROM CrimeIncident LIMIT 5;")
    incidents = cursor.fetchall()
    print("Sample Crime Incidents:")
    for incident in incidents:
        print(f"{incident['incident_id']} - {incident['description']}")
        
    cursor.execute("SELECT COUNT(*) FROM CrimeIncident;")
    incident_count = cursor.fetchone()
    print(f"Total Crime Incidents: {incident_count[0]}")
    
    # Organization = Bengaluru North Gang
    cursor.execute("SELECT * FROM Organization WHERE organization_name = 'Bengaluru North Gang';")
    gang = cursor.fetchone()
    print("Gang Organization:")
    print(f"{gang['organization_id']} - {gang['organization_name']}")
    
    # Accused Persons
    cursor.execute("""
            SELECT person_id, COUNT(*)
            FROM CrimeParticipant
            WHERE role = 'Accused'
            GROUP BY person_id
            ORDER BY COUNT(*) DESC
            LIMIT 10;
            """)
    accused_counts = cursor.fetchall()
    print("Top 10 Accused Persons by Incident Count:")
    for accused in accused_counts:
        print(f"Person ID: {accused['person_id']} - Incidents: {accused['COUNT(*)']}")
        
    conn.close()
    
    
if __name__ == "__main__":
    # seed_all()
    test_query()
