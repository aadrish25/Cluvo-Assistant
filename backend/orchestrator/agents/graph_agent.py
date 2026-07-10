from agno.agent import Agent
from agno.run import RunContext
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

DATABASE_PATH = BASE_DIR / "database" / "ksp_crime_platform.db"
GRAPH_ARTIFACT = BASE_DIR / "graph_artifacts"
GRAPH_ARTIFACT.mkdir(parents=True,exist_ok=True)

from backend.orchestrator.prompts.graph_agent_prompt import GRAPH_AGENT_SYSTEM_PROMPT
from backend.orchestrator.llm import gemma4_31b
from backend.database import create_connection
from backend.database import memory_db
import networkx as nx
from pyvis.network import Network


# tool to make primary person node -> the node around whom the network is centered
def create_network_centered_around_person(run_context:RunContext,person_name:str):
    """
    Build person-centered NetworkX graphs for people matching a name.

    Args:
        context (RunContext): Agent run context. This tool stores `person_name`
        and the generated `graph_list` in `context.session_state` for later
        visualization.
        person_name (str): Full or partial person name to search, such as
        "Ravi Kumar" or "Deepa Gowda".

    Returns:
        None. The generated graphs are stored in
        `context.session_state["graph_list"]`. If multiple people match the
        name, one graph is created for each matched person.
    """
    
    try:
        conn = create_connection()
        cursor = conn.cursor()

        
        # add the person_name to context
        run_context.session_state["person_name"] = person_name
        
        person_graph_list = [] # in case there are multiple persons with the same name

        person_query = """
        SELECT person_id, first_name, last_name
        FROM Person
        WHERE first_name || ' ' || last_name LIKE ?;
        """
        
        cursor.execute(person_query,(f"%{person_name}%",))
        rows = cursor.fetchall()
        
        # more than one person could have the same name, so build the network for all persons
        for row in rows:
            person_id = row['person_id']
            first_name = row['first_name']
            last_name = row['last_name']
            person_node_name = f"person:{person_id}"
            
            # create Person Node
            G = nx.MultiGraph()
            
            G.add_node(
                person_node_name,
                label=f"{first_name} {last_name}",
                type="Person"
            )
            
            # query incidents involving this person
            incident_query = """
            SELECT
            ci.incident_id,
            f.fir_number,
            cp.role
            FROM CrimeParticipant cp
            JOIN CrimeIncident ci ON ci.incident_id = cp.incident_id
            JOIN FIR f ON f.fir_id = ci.fir_id
            WHERE cp.person_id = ?;
            """
            
            cursor.execute(incident_query,(person_id,))
            incidents = cursor.fetchall()
            
            # for each incident, add a node and connect to person
            for incident in incidents:
                incident_id = incident['incident_id']
                fir_number = incident['fir_number']
                person_role = incident['role'].upper()
                incident_node_name = f"incident:{incident_id}"
                
                # add incident node
                G.add_node(
                    incident_node_name,
                    label=fir_number,
                    type="Incident",
                )
                
                # add edge connecting person to this incident
                G.add_edge(
                    person_node_name,
                    incident_node_name,
                    relation = f"{person_role}_IN"
                )
                
                
            # query co accused with this person in the same incidents
            co_accused_query = """
            SELECT DISTINCT
                p.person_id,
                p.first_name,
                p.last_name,
                f.fir_number
            FROM CrimeParticipant cp_self
            JOIN CrimeParticipant cp_other
                ON cp_self.incident_id = cp_other.incident_id
            JOIN Person p
                ON p.person_id = cp_other.person_id
            JOIN CrimeIncident ci
                ON ci.incident_id = cp_self.incident_id
            JOIN FIR f
                ON f.fir_id = ci.fir_id
            WHERE cp_self.person_id = ?
            AND cp_self.role = 'Accused'
            AND cp_other.role = 'Accused'
            AND cp_other.person_id != cp_self.person_id;
            """
            
            cursor.execute(co_accused_query,(person_id,))
            co_accused_persons = cursor.fetchall()
            
            # for each co accused person, relate it with the primary person
            for person in co_accused_persons:
                co_accused_id = person['person_id']
                co_accused_name = f"{person['first_name']} {person['last_name']}"
                co_accused_node_name = f"person:{co_accused_id}"
                incident_fir = person['fir_number'] # this is the incident in which the person is co accused with main person
                
                # create the co_accused node
                G.add_node(
                    co_accused_node_name,
                    label=co_accused_name,
                    type="Person"
                )
                
                # add edge connecting the co accused with main person
                G.add_edge(
                    person_node_name,
                    co_accused_node_name,
                    relation="CO_ACCUSED_WITH",
                    fir_number = incident_fir,
                )
            
            
            # query the organizations this person is related to
            organization_query = """
            SELECT
                o.organization_id,
                o.organization_name,
                po.role
            FROM PersonOrganization po
            JOIN Organization o ON o.organization_id = po.organization_id
            WHERE po.person_id = ?;
            """
            
            cursor.execute(organization_query,(person_id,))
            organizations = cursor.fetchall()
            
            # connect each organization with the primary person
            for org in organizations:
                org_id = org['organization_id']
                org_name = org['organization_name']
                person_role = org['role']
                org_node_name = f"organization:{org['organization_name']}"
                
                # create the organization node
                G.add_node(
                    org_node_name,
                    label=org_name,
                    type="Organization",
                )
                
                # connect the organization to the primary person
                G.add_edge(
                    person_node_name,
                    org_node_name,
                    relation="MEMBER_OF",
                    role=person_role,
                )
            
            
            
            # query the vehicles used/owned by this person
            vehicle_query = """
            SELECT
                v.vehicle_id,
                v.registration_number,
                v.vehicle_type,
                v.manufacturer,
                v.model,
                v.color,
                pv.ownership_type,
                pv.registered_from,
                pv.registered_to
            FROM PersonVehicle pv
            JOIN Vehicle v ON v.vehicle_id = pv.vehicle_id
            WHERE pv.person_id = ?;
            """
            
            cursor.execute(vehicle_query,(person_id,))
            vehicles = cursor.fetchall()
            
            for vehicle in vehicles:
                vehicle_id = vehicle['vehicle_id']
                registration_number = vehicle['registration_number']
                vehicle_type = vehicle['vehicle_type']
                vehicle_ownership_type = vehicle['ownership_type']
                vehicle_color = vehicle['color']
                vehicle_node_name = f"vehicle:{vehicle_id}"
                
                # add vehicle node
                G.add_node(
                    vehicle_node_name,
                    label=registration_number,
                    type="Vehicle",
                    vehicle_type=vehicle_type,
                    color=vehicle_color,
                )
                
                
                # connect this vehicle to the person
                G.add_edge(
                    person_node_name,
                    vehicle_node_name,
                    relation="USES_VEHICLE",
                    ownership_type=vehicle_ownership_type,
                )
                
            
            
            # query the phones related to this person
            phone_query = """
            SELECT
                ph.phone_id,
                ph.phone_number,
                ph.imei,
                ph.network_provider,
                pp.start_date,
                pp.end_date
            FROM PersonPhone pp
            JOIN Phone ph ON ph.phone_id = pp.phone_id
            WHERE pp.person_id = ?;
            """
            
            cursor.execute(phone_query,(person_id,))
            phones = cursor.fetchall()
            
            for phone in phones:
                phone_id = phone['phone_id']
                phone_number = phone['phone_number']
                phone_imei = phone['imei']
                phone_nw_provider = phone['network_provider']
                end_date = phone['end_date']
                phone_node_name = f"phone:{phone_id}"
                
                
                # create the Node
                G.add_node(
                    phone_node_name,
                    label=phone_number,
                    type="Phone",
                    imei=phone_imei,
                    network_provider=phone_nw_provider,
                )

                # connect this phone to the person
                G.add_edge(
                    person_node_name,
                    phone_node_name,
                    relation="USES_PHONE",
                    active=end_date is None,
                )
                
                
            # query the bank accounts related to this person
            bank_acc_query = """
            SELECT
                ba.account_id,
                ba.bank_name,
                ba.account_number,
                ba.ifsc,
                ba.account_type,
                pba.relation_type
            FROM PersonBankAccount pba
            JOIN BankAccount ba ON ba.account_id = pba.account_id
            WHERE pba.person_id = ?;
            """
            
            cursor.execute(bank_acc_query,(person_id,))
            bank_accounts = cursor.fetchall()
            
            for acc in bank_accounts:
                account_id = acc['account_id']
                account_number = acc['account_number']
                bank_name = acc['bank_name']
                account_type = acc['account_type']
                acc_relation_type = acc['relation_type']
                acc_node_label = f"{bank_name} {account_number[-4:]}"
                acc_node_name = f"account:{account_id}"
                
                # create account node
                G.add_node(
                    acc_node_name,
                    label=acc_node_label,
                    type="BankAccount",
                    bank_name=bank_name,
                    account_type=account_type,
                )
                
                # connect this account to the person
                G.add_edge(
                    person_node_name,
                    acc_node_name,
                    relation="HAS_ACCOUNT_IN",
                    relation_type=acc_relation_type,
                )            
            
            
            # also query the transactions this person has made
            account_ids = [acc["account_id"] for acc in bank_accounts]
            if account_ids:
                placeholders = ",".join(["?"] * len(account_ids))
                transaction_query = f"""
                SELECT
                    ft.transaction_id,
                    ft.from_account_id,
                    ft.to_account_id,
                    ft.amount,
                    ft.transaction_date,
                    ft.transaction_type,
                    ft.remarks,
                    from_ba.bank_name AS from_bank_name,
                    from_ba.account_number AS from_account_number,
                    from_ba.account_type AS from_account_type,
                    to_ba.bank_name AS to_bank_name,
                    to_ba.account_number AS to_account_number,
                    to_ba.account_type AS to_account_type
                FROM FinancialTransaction ft
                JOIN BankAccount from_ba ON from_ba.account_id = ft.from_account_id
                JOIN BankAccount to_ba ON to_ba.account_id = ft.to_account_id
                WHERE ft.from_account_id IN ({placeholders})
                   OR ft.to_account_id IN ({placeholders});
                """

                cursor.execute(transaction_query, account_ids + account_ids)
                transactions = cursor.fetchall()

                for transaction in transactions:
                    from_account_id = transaction["from_account_id"]
                    to_account_id = transaction["to_account_id"]
                    from_account_node_name = f"account:{from_account_id}"
                    to_account_node_name = f"account:{to_account_id}"

                    G.add_node(
                        from_account_node_name,
                        label=f"{transaction['from_bank_name']} {transaction['from_account_number'][-4:]}",
                        type="BankAccount",
                        bank_name=transaction["from_bank_name"],
                        account_type=transaction["from_account_type"],
                    )

                    G.add_node(
                        to_account_node_name,
                        label=f"{transaction['to_bank_name']} {transaction['to_account_number'][-4:]}",
                        type="BankAccount",
                        bank_name=transaction["to_bank_name"],
                        account_type=transaction["to_account_type"],
                    )

                    G.add_edge(
                        from_account_node_name,
                        to_account_node_name,
                        relation="TRANSFERRED_TO",
                        transaction_id=transaction["transaction_id"],
                        amount=transaction["amount"],
                        transaction_date=transaction["transaction_date"],
                        transaction_type=transaction["transaction_type"],
                        remarks=transaction["remarks"],
                    )
                    
            person_graph_list.append(G)
        
        
        # add the graph list to context
        run_context.session_state["graph_list"] = [nx.node_link_data(graph) for graph in person_graph_list] # convert it into JSON serializable format, so that it can be saved into session
        run_context.session_state["graph_count"] = len(person_graph_list)
            
        print(f"[GRAPH AGENT] Person graph list created successfully!")
        
    except Exception as e:
        print(f"[GRAPH AGENT] Could not create primary person node: {e}")
        
        

def save_person_network_html(run_context:RunContext):
    """
    Save generated person-network graphs as interactive HTML files.

    Args:
        context (RunContext): Agent run context containing
        `context.session_state["person_name"]` and
        `context.session_state["graph_list"]`, created by
        `create_network_centered_around_person`.

    Returns:
        None. Writes one HTML file per graph into `graph_artifacts/`, using the
        searched person name and graph index in the filename.
    """
    try:
        
        # take the person name and graph list from the context/session state
        person_name = run_context.session_state["person_name"]
        graph_list_json = run_context.session_state["graph_list"]
        
        graph_list = [nx.node_link_graph(graph,multigraph=True) for graph in graph_list_json]
        
        
        net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="#111111")

        colors = {
            "Person": "#2563eb",
            "Incident": "#f97316",
            "Organization": "#dc2626",
            "Vehicle": "#16a34a",
            "Phone": "#9333ea",
            "BankAccount": "#0891b2",
        }

        for i,G in enumerate(graph_list,start=1):
            for node_id, attrs in G.nodes(data=True):
                net.add_node(
                    node_id,
                    label=attrs.get("label", node_id),
                    title=str(attrs),
                    color=colors.get(attrs.get("type"), "#64748b"),
                )

            for source, target, attrs in G.edges(data=True):
                net.add_edge(
                    source,
                    target,
                    label=attrs.get("relation", ""),
                    title=str(attrs),
                )

            file_path = GRAPH_ARTIFACT / f"{person_name}_{i}.html"
            
            run_context.session_state["graph_html_paths"].append(str(file_path))
                            
            net.write_html(str(file_path))
        
    except Exception as e:
        print(f"[GRAPH AGENT] Failed to save person network: {e}")
        
        
        
# create the graph agent
def create_graph_agent():
    try:
        return Agent(
          model = gemma4_31b,
          name = "Graph Agent",
          description = "An agent that builds and saves relationship graphs, for a person on the KSP Crime Database.",
          system_message = GRAPH_AGENT_SYSTEM_PROMPT,
          tools = [
              create_network_centered_around_person,
              save_person_network_html
          ],
          reasoning = True,
          db=memory_db,
          reasoning_min_steps = 3,
          reasoning_max_steps = 7,
          add_history_to_context=False,
          add_session_state_to_context=True,
          telemetry=True,
          debug_mode = True
        )
    except Exception as e:
        print(f"[GRAPH AGENT] Error in creating graph agent: {e}")
        
if __name__ == "__main__":
    graph_list = create_network_centered_around_person(person_name="Deepa Gowda")
    
