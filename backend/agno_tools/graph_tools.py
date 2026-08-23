from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

import re
from agno.run import RunContext
import networkx as nx
from pyvis.network import Network
from backend.database import create_connection
from backend.config import GRAPH_DIR



def find_matching_person(run_context:RunContext,person_name:str):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        person_query = """
        SELECT person_id, first_name, last_name
        FROM Person
        WHERE first_name || ' ' || last_name LIKE ?;
        """
        
        cursor.execute(person_query,(f"%{person_name}%",))
        matched_rows = cursor.fetchall()
        
        matched_candidates = [
            dict(row) 
            for row in matched_rows
        ]
        
        run_context.session_state["matched_person_names"] = [f"{person.get('first_name')} {person.get('last_name')}" for person in matched_candidates]
        
        return matched_candidates
    
    except Exception as e:
        print(f"[GRAPH AGENT] Exception in finding matching persons: {e}")
        return {
            "type":"error",
            "message":"Ran into an unknown error."
        }
        

# tool to make primary person node -> the node around whom the network is centered
def create_network_centered_around_person(run_context:RunContext,person_id:str = None):
    """
    Build and save a person-centered NetworkX graph for one resolved person.

    Args:
        context (RunContext): Agent run context. This tool stores the resolved
        `chosen_person_id` and the generated graph payload in
        `context.session_state` for later use.
        person_id (str): The resolved person_id for the single person whose
        network should be built.

    Returns:
        str: A confirmation message indicating that the graph HTML file was
        generated and saved under the graph artifacts folder.
    """
    
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        state_ids = (run_context.session_state or {}).get("person_ids") or []
        if len(state_ids) == 1:
            person_id = state_ids[0]
            run_context.session_state["chosen_person_id"] = person_id
        elif not person_id:
            return {
                "type": "error",
                "message": "No single resolved person_id available.Resolve the person first."
            }
            
        
        person_graph_list = [] # in case there are multiple persons with the same name

        person_query = """
        SELECT person_id, first_name, last_name
        FROM Person
        WHERE person_id = ?;
        """
        
        cursor.execute(person_query,(person_id,))
        matched_person_row = cursor.fetchall()
        
        print(f"[GRAPH AGENT] Matched person row: {matched_person_row}")
        matched_person_row = matched_person_row[0]
        
        person_id = matched_person_row['person_id']
        first_name = matched_person_row['first_name']
        last_name = matched_person_row['last_name']
        chosen_person_name = f"{first_name} {last_name}"
        person_node_name = f"person:{person_id}"
        
        run_context.session_state["chosen_person_name"] = f"{first_name} {last_name}"
            
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
        run_context.session_state["generated_graph"] = nx.node_link_data(G) # convert it into JSON serializable format, so that it can be saved into session
        
         # --- save HTML directly from the in-memory G, no round trip needed ---
        net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="#111111")
 
        colors = {
            "Person": "#2563eb",
            "Incident": "#f97316",
            "Organization": "#dc2626",
            "Vehicle": "#16a34a",
            "Phone": "#9333ea",
            "BankAccount": "#0891b2",
        }
 
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
 
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", chosen_person_name).strip("_")
        file_path = GRAPH_DIR / f"{safe_name}_{person_id[:10]}_network.html"
 
        # Defensive: don't assume the key already exists as a list
        run_context.session_state.setdefault("graph_html_path", []).append(str(file_path))
 
        net.write_html(str(file_path))
        print(f"[GRAPH AGENT] Person graph list created successfully!")
 
        return f"Criminal network for {chosen_person_name} generated and saved to {file_path}."
 
    except Exception as e:
        error_msg = f"Failed to build/save person network for person_id={person_id}: {e}"
        print(f"[GRAPH AGENT] {error_msg}")
        return error_msg
    
    

# not used now, the create graph tool handles this internally
def save_person_network_html(run_context:RunContext):
    """
    Legacy helper retained for compatibility. The current flow writes the HTML
    artifact directly inside `create_network_centered_around_person`, so this
    function is no longer required by the agent.
    """
    try:
        
        # take the person name and graph list from the context/session state
        person_name = run_context.session_state["chosen_person_name"]
        graph_json = run_context.session_state["generated_graph"]
        
        G = nx.node_link_graph(graph_json,multigraph=True) 
        
        
        net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="#111111")

        colors = {
            "Person": "#2563eb",
            "Incident": "#f97316",
            "Organization": "#dc2626",
            "Vehicle": "#16a34a",
            "Phone": "#9333ea",
            "BankAccount": "#0891b2",
        }

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

        file_path = GRAPH_DIR / f"{person_name}_network.html"
        
        run_context.session_state["graph_html_path"].append(str(file_path))
                        
        net.write_html(str(file_path))
        
        return "Criminal network generated successfully!"
        
    except Exception as e:
        print(f"[GRAPH AGENT] Failed to save person network: {e}")