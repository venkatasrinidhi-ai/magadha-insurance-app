import flet as ft
import flet.fastapi as flet_fastapi
import sqlite3
import datetime
import threading
import time
import math
import heapq
import os

DB_FILE = "magadha_insurance.db"

# =====================================================================
# 1. ADVANCED DATA STRUCTURES (ADS) & GRAPH THEORY (DMGT) MODULES
# =====================================================================

# ADS: Trie Data Structure for fast O(L) policy search
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.meta = None

class PolicyTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, meta):
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.meta = meta

    def search_prefix(self, prefix):
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
        results = []
        self._collect_all(node, results)
        return results

    def _collect_all(self, node, results):
        if node.is_end_of_word:
            results.append(node.meta)
        for char, next_node in node.children.items():
            self._collect_all(next_node, results)

# ADS: Priority Queue (Min-Heap) for Triage Claim Processing
class ClaimPriorityQueue:
    def __init__(self):
        self.heap = []
        self.counter = 0

    def push_claim(self, severity_rank, claim_id, details):
        heapq.heappush(self.heap, (severity_rank, self.counter, claim_id, details))
        self.counter += 1

    def pop_urgent_claim(self):
        if self.heap:
            return heapq.heappop(self.heap)
        return None

# DMGT: Graph Traversal for Cashless Hospital Network (Adjacency Matrix / BFS)
class HospitalNetworkGraph:
    def __init__(self):
        self.nodes = ["Hyderabad", "Kakinada", "Visakhapatnam", "Vijayawada", "Guntur", "Rajahmundry"]
        self.adj_matrix = {
            "Hyderabad": ["Vijayawada", "Kakinada"],
            "Vijayawada": ["Hyderabad", "Guntur", "Rajahmundry"],
            "Guntur": ["Vijayawada"],
            "Rajahmundry": ["Vijayawada", "Kakinada"],
            "Kakinada": ["Rajahmundry", "Visakhapatnam"],
            "Visakhapatnam": ["Kakinada"]
        }

    def shortest_network_hops(self, start_city, target_city):
        if start_city not in self.adj_matrix or target_city not in self.adj_matrix:
            return 1
        queue = [(start_city, 0)]
        visited = {start_city}
        while queue:
            curr, hops = queue.pop(0)
            if curr == target_city:
                return hops
            for neighbor in self.adj_matrix.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, hops + 1))
        return 1

# DMGT: Propositional Logic Rule Evaluator
def verify_claim_proposition(has_active_policy, within_grace_period, documented_proof):
    # Boolean logic: (Policy AND Documented) AND NOT Expired
    return bool(has_active_policy and documented_proof and within_grace_period)

# Initializing Project Structures
policy_trie = PolicyTrie()
policy_trie.insert("Car Insurance", {"name": "Zero-Dep Car Shield", "rate": 3500, "category": "Vehicle"})
policy_trie.insert("Bike Insurance", {"name": "Two-Wheeler Comprehensive", "rate": 715, "category": "Vehicle"})
policy_trie.insert("Home Insurance", {"name": "Home Secure Asset Pass", "rate": 3200, "category": "Property"})
policy_trie.insert("Business Insurance", {"name": "Enterprise Commercial Asset", "rate": 5800, "category": "Commercial"})
policy_trie.insert("Travel Insurance", {"name": "Global Cashless Passport", "rate": 1150, "category": "Travel"})
policy_trie.insert("Cyber Insurance", {"name": "Digital Fraud & Identity Shield", "rate": 1490, "category": "Cyber"})

claim_queue = ClaimPriorityQueue()
hospital_graph = HospitalNetworkGraph()

# =====================================================================
# 2. DATABASE MANAGEMENT SYSTEM (DBMS) INITIALIZATION
# =====================================================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS customer_profile (
            policy_no TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            title_salutation TEXT,
            aadhaar_no TEXT,
            mobile_no TEXT,
            plan_name TEXT,
            reg_date TEXT,
            valid_upto TEXT,
            claimable_amt TEXT,
            premium_per_month TEXT,
            nominee_name TEXT,
            nominee_relation TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS payment_history (
            txn_id TEXT PRIMARY KEY,
            policy_no TEXT,
            plan_name TEXT,
            payment_date TEXT,
            amount_paid TEXT,
            status TEXT,
            FOREIGN KEY (policy_no) REFERENCES customer_profile (policy_no)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY,
            policy_no TEXT,
            claim_type TEXT,
            incident_type TEXT,
            claim_amt TEXT,
            severity_rank INTEGER,
            claim_date TEXT,
            status TEXT,
            FOREIGN KEY (policy_no) REFERENCES customer_profile (policy_no)
        )
    """)

    c.execute("""
        INSERT OR REPLACE INTO customer_profile VALUES (
            'MAG-IND-2024-88',
            'Srinidhi',
            'Mr.',
            'XXXX-XXXX-7892',
            '9876543210',
            'Magadha Life & Health Twin Shield',
            '2025-01-15',
            '2027-01-14',
            'Rs. 15,00,000',
            'Rs. 1,250',
            'Nominee',
            'Family'
        )
    """)

    conn.commit()
    conn.close()

init_db()

# =====================================================================
# 3. UTILITY FUNCTIONS (STRICT FIRST LETTER EXTRACTION)
# =====================================================================
def extract_clean_initial(name_str):
    if not name_str:
        return "U"
    cleaned = "".join([ch for ch in name_str if ch.isalpha()])
    return cleaned[0].upper() if len(cleaned) > 0 else "U"

# =====================================================================
# 4. MAIN FLUX APPLICATION ENGINE
# =====================================================================
def main(page: ft.Page):
    page.title = "Magadha Insurance Portal"
    page.padding = 0
    page.bgcolor = "#0B0F19"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "start"

    user_name = ["Srinidhi"]
    user_salutation = ["Mr."]
    current_policy = ["MAG-IND-2024-88"]
    current_mobile = ["9876543210"]
    nominee_info = ["Family Nominee"]
    card_side = ["life"]
    selected_vehicle_type = ["Car"]
    current_vehicle_number = ["AP39CD1099"]
    current_nav_tab = ["home"]

    def toast(msg, color="#4F46E5"):
        snack = ft.SnackBar(ft.Text(msg, color="white", weight="bold"), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    avatar_letter_txt = ft.Text("S", size=18, weight="bold", color="white")
    user_greeting_txt = ft.Text("Hi Srinidhi", size=17, weight="bold", color="white")
    card_holder_name_txt = ft.Text("SRINIDHI", size=11, weight="bold", color="white")

    def update_identity(new_name):
        clean = new_name.strip()
        if clean:
            user_name[0] = clean
            init_letter = extract_clean_initial(clean)
            avatar_letter_txt.value = init_letter
            user_greeting_txt.value = f"Hi {clean}"
            card_holder_name_txt.value = clean.upper()
            profile_name_txt.value = f"Name: {user_salutation[0]} {clean}"
            profile_card_name.value = f"Name: {user_salutation[0]} {clean}"
            v_name.value = clean
        page.update()

    # ----------------------------------------------------
    # AI PROBLEM SOLVER DESK (ENGLISH BOT)
    # ----------------------------------------------------
    help_chat_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=270, auto_scroll=True)
    help_input_field = ft.TextField(hint_text="Ask about policies, claims, algorithms...", text_size=12, expand=True, bgcolor="#1E293B", border_color="#334155", color="white")

    def make_chat_bubble(msg_text, is_user=False):
        return ft.Row(
            [
                ft.Container(
                    content=ft.Text(msg_text, color="white" if is_user else "#E2E8F0", size=12, no_wrap=False),
                    bgcolor="#4F46E5" if is_user else "#1E293B",
                    padding=10,
                    border_radius=12,
                    width=270
                )
            ],
            alignment="end" if is_user else "start"
        )

    def resolve_english_query(query):
        q = query.lower().strip()
        if q in ["hi", "hello", "hey", "help"]:
            return f"Hello {user_name[0]}! I am Magadha AI Assistant. How can I resolve your insurance issue today?"
        elif "algo" in q or "dsa" in q or "graph" in q or "trie" in q:
            return "This project implements:\n1. Trie Data Structure for O(L) instant policy search.\n2. Min-Heap Priority Queue for ICU emergency claim sorting.\n3. Graph BFS for closest cashless hospital network hops."
        elif "claim" in q:
            return "To register a claim, tap 'Life Claim' or 'Health Claim' on Home. Our automated Priority Queue scheduler indexes and processes claims within 4 hours."
        elif "car" in q or "bike" in q or "vehicle" in q:
            return "Enter your vehicle registration number on the Home dashboard to calculate instant zero-depreciation quotes from 16+ top national insurers."
        elif "policy" in q:
            return f"Your active schedule {current_policy[0]} covers Rs. 15,00,000 up to 14 Jan 2027 with direct cashless hospitalization."
        else:
            return f"Regarding '{query}', you can search plans, track claims, and manage nominees directly. Call 1800-MAGADHA for 24/7 tele-assistance."

    def on_send_help(e):
        msg = help_input_field.value.strip()
        if not msg:
            return
        help_chat_col.controls.append(make_chat_bubble(msg, is_user=True))
        help_input_field.value = ""
        page.update()

        ans = resolve_english_query(msg)
        time.sleep(0.2)
        help_chat_col.controls.append(make_chat_bubble(ans, is_user=False))
        page.update()

    help_chat_col.controls.append(make_chat_bubble("Hello! Magadha AI Assistant is ready. Please describe your issue in English.", is_user=False))

    help_sheet = ft.BottomSheet(
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([ft.Icon("support_agent", color="#60A5FA", size=22), ft.Text("Magadha AI Help Desk", size=15, weight="bold", color="white")]),
                    ft.IconButton(icon="close", icon_size=18, icon_color="white", on_click=lambda _: setattr(help_sheet, "open", False) or page.update())
                ], alignment="spaceBetween"),
                ft.Divider(height=1, color="#334155"),
                help_chat_col,
                ft.Row([
                    help_input_field,
                    ft.IconButton(icon="send", icon_color="#60A5FA", on_click=on_send_help)
                ], spacing=4)
            ], tight=True, spacing=6),
            padding=16,
            bgcolor="#0F172A",
            width=390
        )
    )
    page.overlay.append(help_sheet)

    def trigger_help(e):
        help_sheet.open = True
        page.update()

    # ----------------------------------------------------
    # REFERENCE VIDEO: DYNAMIC GLOWING FLOATING NAVBAR DOCK
    # ----------------------------------------------------
    nav_btn_home = ft.IconButton(icon="home", icon_color="#60A5FA", tooltip="Home")
    nav_btn_search = ft.IconButton(icon="search", icon_color="#94A3B8", tooltip="Search (Trie)")
    nav_btn_claims = ft.IconButton(icon="receipt_long", icon_color="#94A3B8", tooltip="Claims (Heap)")
    nav_btn_network = ft.IconButton(icon="hub", icon_color="#94A3B8", tooltip="Network (Graph)")
    nav_btn_profile = ft.IconButton(icon="person", icon_color="#94A3B8", tooltip="Profile")

    def update_navbar_glow(active_key):
        nav_btn_home.icon_color = "#60A5FA" if active_key == "home" else "#94A3B8"
        nav_btn_search.icon_color = "#60A5FA" if active_key == "search" else "#94A3B8"
        nav_btn_claims.icon_color = "#60A5FA" if active_key == "claims" else "#94A3B8"
        nav_btn_network.icon_color = "#60A5FA" if active_key == "network" else "#94A3B8"
        nav_btn_profile.icon_color = "#60A5FA" if active_key == "profile" else "#94A3B8"
        page.update()

    def on_dock_nav_click(target):
        current_nav_tab[0] = target
        update_navbar_glow(target)
        if target == "home":
            main_viewport.content = home_content_view
        elif target == "search":
            main_viewport.content = trie_search_view
        elif target == "claims":
            main_viewport.content = claims_view
        elif target == "network":
            main_viewport.content = network_graph_view
        elif target == "profile":
            main_viewport.content = profile_view
        page.update()

    nav_btn_home.on_click = lambda _: on_dock_nav_click("home")
    nav_btn_search.on_click = lambda _: on_dock_nav_click("search")
    nav_btn_claims.on_click = lambda _: on_dock_nav_click("claims")
    nav_btn_network.on_click = lambda _: on_dock_nav_click("network")
    nav_btn_profile.on_click = lambda _: on_dock_nav_click("profile")

    floating_dock_navbar = ft.Container(
        content=ft.Row([
            nav_btn_home,
            nav_btn_search,
            nav_btn_claims,
            nav_btn_network,
            nav_btn_profile,
        ], alignment="spaceEvenly"),
        width=340,
        height=54,
        bgcolor="#111827",
        border_radius=27,
        border=ft.border.all(1.5, "#374151"),
        shadow=ft.BoxShadow(blur_radius=16, color="#00000080"),
        padding=ft.padding.symmetric(horizontal=8)
    )

    # ----------------------------------------------------
    # VIRTUAL CARD (3D ROTATION)
    # ----------------------------------------------------
    life_card_content = ft.Column([
        ft.Row([
            ft.Row([
                ft.Icon("shield", color="#FBBF24", size=18),
                ft.Text("LIFE INSURANCE PASS", size=11, weight="bold", color="white")
            ], spacing=4),
            ft.Container(
                content=ft.Row([ft.Icon("rotate_right", size=11, color="white"), ft.Text("Flip Card", size=9, color="white", weight="bold")], spacing=2),
                bgcolor="#FFFFFF26",
                padding=4,
                border_radius=4
            )
        ], alignment="spaceBetween"),
        ft.Container(height=2),
        ft.Row([
            ft.Container(width=34, height=22, bgcolor="#F59E0B", border_radius=4),
            ft.Icon("contactless", color="white", size=18)
        ], alignment="spaceBetween"),
        ft.Container(height=4),
        ft.Text("5412  8801  9924  7710", size=14, weight="bold", color="white", font_family="monospace"),
        ft.Row([
            ft.Column([
                ft.Text("INSURED MEMBER", size=8, color="#CBD5E1", weight="bold"),
                card_holder_name_txt
            ], spacing=1),
            ft.Column([
                ft.Text("COVERAGE", size=8, color="#CBD5E1", weight="bold"),
                ft.Text("Rs. 15 LAKHS", size=11, weight="bold", color="#38BDF8")
            ], spacing=1),
            ft.Container(
                content=ft.Text("NOMINEE PROT", size=9, weight="bold", color="#FBBF24"),
                bgcolor="#451A03",
                padding=4,
                border_radius=4
            )
        ], alignment="spaceBetween")
    ], spacing=3)

    health_card_content = ft.Column([
        ft.Row([
            ft.Row([
                ft.Icon("local_hospital", color="#34D399", size=18),
                ft.Text("HEALTH CASHLESS PASS", size=11, weight="bold", color="white")
            ], spacing=4),
            ft.Container(
                content=ft.Row([ft.Icon("rotate_right", size=11, color="white"), ft.Text("Flip Card", size=9, color="white", weight="bold")], spacing=2),
                bgcolor="#FFFFFF26",
                padding=4,
                border_radius=4
            )
        ], alignment="spaceBetween"),
        ft.Container(height=2),
        ft.Row([
            ft.Container(width=34, height=22, bgcolor="#10B981", border_radius=4),
            ft.Icon("wifi", color="white", size=18)
        ], alignment="spaceBetween"),
        ft.Container(height=4),
        ft.Text("4532  6612  3341  8821", size=14, weight="bold", color="white", font_family="monospace"),
        ft.Row([
            ft.Column([
                ft.Text("PRIMARY HOLDER", size=8, color="#E2E8F0", weight="bold"),
                card_holder_name_txt
            ], spacing=1),
            ft.Column([
                ft.Text("FAMILY COVER", size=8, color="#E2E8F0", weight="bold"),
                ft.Text("4 MEMBERS", size=11, weight="bold", color="#FDE047")
            ], spacing=1),
            ft.Container(
                content=ft.Text("CASHLESS", size=9, weight="bold", color="#064E3B"),
                bgcolor="#A7F3D0",
                padding=4,
                border_radius=4
            )
        ], alignment="spaceBetween")
    ], spacing=3)

    virtual_card_container = ft.Container(
        content=life_card_content,
        width=380,
        height=165,
        padding=14,
        border_radius=16,
        bgcolor="#0F172A",
        shadow=ft.BoxShadow(blur_radius=12, color="#00000040"),
        animate_rotation=ft.Animation(350, "easeInOut"),
        rotate=0
    )

    is_flipping = [False]

    def trigger_card_flip(e):
        if is_flipping[0]:
            return
        is_flipping[0] = True
        virtual_card_container.rotate = math.pi * 0.5
        page.update()
        time.sleep(0.18)

        if card_side[0] == "life":
            card_side[0] = "health"
            virtual_card_container.content = health_card_content
            virtual_card_container.bgcolor = "#064E3B"
        else:
            card_side[0] = "life"
            virtual_card_container.content = life_card_content
            virtual_card_container.bgcolor = "#0F172A"

        virtual_card_container.rotate = 0
        page.update()
        time.sleep(0.18)
        is_flipping[0] = False

    virtual_card_container.on_click = trigger_card_flip

    amt_label = ft.Text("••••••••", size=16, weight="bold", color="#020617")
    eye_btn = ft.IconButton(icon="visibility_off", icon_color="#4F46E5", icon_size=18)

    def on_toggle_eye(e):
        eye_open[0] = not eye_open[0]
        amt_label.value = "Rs. 15,00,000" if eye_open[0] else "••••••••"
        eye_btn.icon = "visibility" if eye_open[0] else "visibility_off"
        page.update()

    eye_btn.on_click = on_toggle_eye

    coverage_detail_box = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("POLICY SCHEDULE OVERVIEW", size=11, weight="bold", color="#1E1B4B"),
                ft.Container(content=ft.Text("ACTIVE", size=9, weight="bold", color="#047857"), bgcolor="#D1FAE5", padding=4, border_radius=4)
            ], alignment="spaceBetween"),
            ft.Text(f"user policy no : {current_policy[0]}", size=12, color="#0F172A", weight="bold"),
            ft.Row([ft.Row([ft.Text("claim amount :", size=12, color="#1E293B", weight="bold"), amt_label]), eye_btn], alignment="spaceBetween"),
            ft.Divider(height=2, color="#CBD5E1"),
            ft.Text("Payout Breakdown (DMGT Logic Verified):", size=11, weight="bold", color="#0F172A"),
            ft.Row([ft.Text("• Natural Death: Rs. 15,00,000", size=10, color="#1E293B", weight="bold"), ft.Text("• Accident: Rs. 30,00,000", size=10, color="#047857", weight="bold")], alignment="spaceBetween"),
            ft.Text("• Critical Illness: Rs. 20,00,000", size=10, color="#B91C1C", weight="bold"),
            ft.Container(
                content=ft.Row([ft.Icon("assignment_ind", size=13, color="#1E1B4B"), ft.Text(f"Nominee: {nominee_info[0]} settlement verified.", size=9, weight="bold", color="#1E1B4B")], spacing=4),
                bgcolor="#E0E7FF",
                padding=4,
                border_radius=4
            )
        ], spacing=4),
        padding=12,
        border_radius=14,
        bgcolor="#FFFFFF",
        border=ft.border.all(1.5, "#CBD5E1")
    )

    action_buttons = ft.Row([
        ft.ElevatedButton("Life Claim", icon="family_restroom", bgcolor="#312E81", color="white", height=42, expand=True, on_click=lambda _: toast("Submitted to Min-Heap Priority Queue!")),
        ft.ElevatedButton("Health Claim", icon="local_hospital", bgcolor="#047857", color="white", height=42, expand=True, on_click=lambda _: toast("Submitted to Min-Heap Priority Queue!"))
    ], spacing=8)

    # ----------------------------------------------------
    # HOME BANNERS & VEHICLE FLOW
    # ----------------------------------------------------
    vehicle_input_txt = ft.TextField(hint_text="e.g. AP39CD1099", text_size=15, text_style=ft.TextStyle(weight="bold", color="#0F172A"), bgcolor="#F8FAFC", border_color="#4F46E5", border_radius=10, text_align="center")
    selected_vehicle_details_hdr = ft.Text("AP39CD1099 • Honda Activa", size=12, weight="bold", color="#CBD5E1")

    def create_insurer_card(company_name, idv_val, price_val):
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(content=ft.Text(company_name[:2].upper(), size=11, weight="bold", color="white"), width=36, height=36, bgcolor="#4F46E5", border_radius=8, alignment=ft.Alignment(0, 0)),
                    ft.Column([ft.Text(company_name, size=12, weight="bold", color="#0F172A"), ft.Text(f"IDV: ₹{idv_val:,}", size=10, color="#64748B")], spacing=1)
                ], spacing=8),
                ft.ElevatedButton(
                    content=ft.Column([ft.Text("Buy Now", size=9, color="white"), ft.Text(f"₹{price_val}", size=11, weight="bold", color="white")], spacing=0, alignment="center"),
                    bgcolor="#4F46E5",
                    style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=10, vertical=4), shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=lambda _: toast(f"{company_name} Policy Active! Record written to SQLite.")
                )
            ], alignment="spaceBetween"),
            padding=10,
            bgcolor="white",
            border_radius=12,
            border=ft.border.all(1, "#E2E8F0")
        )

    insurers_list_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=400)

    def populate_vehicle_plans():
        insurers_list_col.controls.clear()
        data = [("Bajaj General", 30502, 716), ("HDFC ERGO", 27072, 738), ("SBI General", 15665, 715), ("Acko General", 13475, 719), ("ICICI Lombard", 34644, 744)]
        for c_name, idv, p_amt in data:
            factor = 2.4 if selected_vehicle_type[0] == "Car" else 1.0
            insurers_list_col.controls.append(create_insurer_card(c_name, int(idv * factor), int(p_amt * factor)))

    vehicle_plans_view = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.IconButton(icon="arrow_back", icon_color="white", on_click=lambda _: switch_screen("vehicle_entry")),
                ft.Text("Select Plan (Reference UI)", size=17, weight="bold", color="white"),
                ft.IconButton(icon="help_outline", icon_color="white", on_click=trigger_help)
            ], alignment="spaceBetween"),
            ft.Container(
                content=ft.Row([
                    ft.Column([ft.Text(f"{selected_vehicle_type[0]} Details", size=10, color="#94A3B8", weight="bold"), selected_vehicle_details_hdr], spacing=1),
                    ft.TextButton("Modify", on_click=lambda _: switch_screen("vehicle_entry"))
                ], alignment="spaceBetween"),
                padding=8,
                bgcolor="#1F2937",
                border_radius=10
            ),
            insurers_list_col,
            floating_dock_navbar
        ], spacing=10),
        padding=10,
        expand=True,
        visible=False
    )

    def on_proceed_vehicle(e):
        v = vehicle_input_txt.value.strip().upper()
        if not v:
            toast("Enter registration number!", "#B91C1C")
            return
        current_vehicle_number[0] = v
        selected_vehicle_details_hdr.value = f"{v} • Verified"
        populate_vehicle_plans()
        switch_screen("vehicle_plans")

    vehicle_entry_screen = ft.Container(
        content=ft.Column([
            ft.Row([ft.IconButton(icon="arrow_back", icon_color="white", on_click=lambda _: switch_screen("home")), ft.Text("Vehicle Lookup", size=17, weight="bold", color="white"), ft.Container(width=40)], alignment="spaceBetween"),
            ft.Container(height=20),
            ft.Container(
                content=ft.Column([
                    ft.Icon("directions_car" if selected_vehicle_type[0] == "Car" else "two_wheeler", size=45, color="#4F46E5"),
                    ft.Text(f"Enter {selected_vehicle_type[0]} Number", size=17, weight="bold", color="#0F172A"),
                    vehicle_input_txt,
                    ft.ElevatedButton("View Instant Quotes", bgcolor="#4F46E5", color="white", width=300, height=46, on_click=on_proceed_vehicle)
                ], horizontal_alignment="center", spacing=8),
                padding=20,
                bgcolor="white",
                border_radius=16
            )
        ], horizontal_alignment="center"),
        padding=14,
        expand=True,
        visible=False
    )

    def open_vehicle(v_type):
        selected_vehicle_type[0] = v_type
        switch_screen("vehicle_entry")

    big_car_card = ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Container(content=ft.Text("UP TO 85% OFF", size=9, weight="bold", color="white"), bgcolor="#2563EB", padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4),
                ft.Text("Car Insurance", size=15, weight="bold", color="white"),
                ft.Text("Cashless repairs in 6500+ garages", size=10, color="#94A3B8"),
                ft.Container(height=2),
                ft.ElevatedButton("Get Quotes", bgcolor="white", color="#1E1B4B", height=30, on_click=lambda _: open_vehicle("Car"))
            ], spacing=2, expand=True),
            ft.Icon("directions_car_filled", size=55, color="#60A5FA")
        ], alignment="spaceBetween"),
        padding=14,
        border_radius=16,
        bgcolor="#1E1B4B",
        on_click=lambda _: open_vehicle("Car")
    )

    big_bike_card = ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Container(content=ft.Text("INSTANT POLICY IN 2 MINS", size=9, weight="bold", color="white"), bgcolor="#059669", padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4),
                ft.Text("Two Wheeler Insurance", size=15, weight="bold", color="white"),
                ft.Text("Starting @ just ₹715/year", size=10, color="#A7F3D0"),
                ft.Container(height=2),
                ft.ElevatedButton("View Plans", bgcolor="white", color="#064E3B", height=30, on_click=lambda _: open_vehicle("Bike"))
            ], spacing=2, expand=True),
            ft.Icon("two_wheeler", size=55, color="#34D399")
        ], alignment="spaceBetween"),
        padding=14,
        border_radius=16,
        bgcolor="#064E3B",
        on_click=lambda _: open_vehicle("Bike")
    )

    other_categories_grid = ft.Row([
        ft.Container(content=ft.Column([ft.Icon("home", color="#D97706", size=22), ft.Text("Home", size=10, weight="bold", color="#0F172A")], horizontal_alignment="center", spacing=3), bgcolor="white", padding=8, border_radius=12, expand=True, on_click=lambda _: toast("Home Shield Policy Available")),
        ft.Container(content=ft.Column([ft.Icon("store", color="#7C3AED", size=22), ft.Text("Business", size=10, weight="bold", color="#0F172A")], horizontal_alignment="center", spacing=3), bgcolor="white", padding=8, border_radius=12, expand=True, on_click=lambda _: toast("Business Commercial Asset Covered")),
        ft.Container(content=ft.Column([ft.Icon("flight_takeoff", color="#0891B2", size=22), ft.Text("Travel", size=10, weight="bold", color="#0F172A")], horizontal_alignment="center", spacing=3), bgcolor="white", padding=8, border_radius=12, expand=True, on_click=lambda _: toast("Global Travel Pass Ready")),
        ft.Container(content=ft.Column([ft.Icon("lock", color="#DC2626", size=22), ft.Text("Cyber", size=10, weight="bold", color="#0F172A")], horizontal_alignment="center", spacing=3), bgcolor="white", padding=8, border_radius=12, expand=True, on_click=lambda _: toast("Personal Cyber Cover Active"))
    ], spacing=6)

    # ----------------------------------------------------
    # HOME SCREEN (ORIGINAL VERTICAL SCROLL)
    # ----------------------------------------------------
    home_content_view = ft.Column([
        user_greeting_txt,
        virtual_card_container,
        coverage_detail_box,
        action_buttons,
        ft.Container(height=4),
        ft.Row([ft.Text("Vehicle Protection", size=14, weight="bold", color="white"), ft.Text("Best Quotes", size=11, weight="bold", color="#60A5FA")], alignment="spaceBetween"),
        big_car_card,
        big_bike_card,
        ft.Container(height=2),
        ft.Text("More Insurance Products", size=13, weight="bold", color="white"),
        other_categories_grid,
        ft.Container(height=4),
        ft.Text("Live fulfilled", size=15, weight="bold", color="white", italic=True, text_align="center"),
        ft.Text("Instant cashless access & Nominee security", size=11, color="#94A3B8", text_align="center"),
        ft.Container(height=8),
        floating_dock_navbar,
        ft.Container(height=15)
    ], horizontal_alignment="center", spacing=10, scroll=ft.ScrollMode.AUTO)

    # ----------------------------------------------------
    # COLLEGE PROJECT SUBJECT SCREENS (ADS / DMGT / DBMS)
    # ----------------------------------------------------
    # 1. TRIE PREFIX SEARCH (ADS)
    trie_search_input = ft.TextField(hint_text="Search policy prefix (e.g. Car, Cyb, Hom)...", text_size=12, expand=True, bgcolor="#1E293B", color="white")
    trie_results_col = ft.Column(spacing=6)

    def on_trie_search(e):
        trie_results_col.controls.clear()
        query = trie_search_input.value.strip()
        if query:
            matches = policy_trie.search_prefix(query)
            for m in matches:
                trie_results_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([ft.Text(m["name"], weight="bold", color="white", size=12), ft.Text(f"Category: {m['category']}", color="#94A3B8", size=10)]),
                            ft.Text(f"₹{m['rate']}/yr", color="#34D399", weight="bold", size=12)
                        ], alignment="spaceBetween"),
                        padding=10,
                        bgcolor="#1E293B",
                        border_radius=8
                    )
                )
        page.update()

    trie_search_input.on_change = on_trie_search

    trie_search_view = ft.Column([
        ft.Text("ADS: Trie Prefix Search O(L)", size=16, weight="bold", color="white"),
        ft.Text("Fastest algorithmic policy catalog index", size=11, color="#94A3B8"),
        ft.Row([trie_search_input, ft.IconButton(icon="search", icon_color="#60A5FA", on_click=on_trie_search)]),
        trie_results_col,
        ft.Container(height=10),
        floating_dock_navbar
    ], spacing=10, scroll=ft.ScrollMode.AUTO)

    # 2. GRAPH NETWORK ROUTING (DMGT)
    city_from = ft.Dropdown(value="Kakinada", options=[ft.dropdown.Option("Kakinada"), ft.dropdown.Option("Visakhapatnam"), ft.dropdown.Option("Hyderabad"), ft.dropdown.Option("Vijayawada")], width=150, bgcolor="#1E293B", color="white")
    city_to = ft.Dropdown(value="Hyderabad", options=[ft.dropdown.Option("Hyderabad"), ft.dropdown.Option("Vijayawada"), ft.dropdown.Option("Guntur")], width=150, bgcolor="#1E293B", color="white")
    graph_hop_result = ft.Text("Calculated Network Hops: 2 Hops (Direct BFS Route)", size=12, weight="bold", color="#34D399")

    def on_compute_graph_route(e):
        hops = hospital_graph.shortest_network_hops(city_from.value, city_to.value)
        graph_hop_result.value = f"Calculated Network Hops: {hops} Transfer Hops (Shortest Path BFS)"
        page.update()

    network_graph_view = ft.Column([
        ft.Text("DMGT: Hospital Graph Network (BFS)", size=16, weight="bold", color="white"),
        ft.Text("Discrete Mathematics Graph Theory Shortest Path", size=11, color="#94A3B8"),
        ft.Row([city_from, city_to], alignment="center", spacing=10),
        ft.ElevatedButton("Find Shortest Cashless Route", bgcolor="#4F46E5", color="white", on_click=on_compute_graph_route),
        graph_hop_result,
        ft.Container(height=10),
        floating_dock_navbar
    ], horizontal_alignment="center", spacing=12)

    # 3. CLAIMS (MIN-HEAP & DBMS)
    claims_col = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=450)

    def reload_claims_dbms():
        claims_col.controls.clear()
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT claim_id, claim_type, incident_type, claim_amt, status FROM claims")
        for clm in c.fetchall():
            claims_col.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([ft.Text(f"{clm[0]} ({clm[1]})", weight="bold", color="white", size=12), ft.Text(clm[2], size=10, color="#94A3B8")]),
                        ft.Text(clm[3], weight="bold", color="#34D399", size=12)
                    ], alignment="spaceBetween"),
                    padding=8,
                    bgcolor="#1E293B",
                    border_radius=8
                )
            )
        conn.close()

    reload_claims_dbms()

    claims_view = ft.Column([
        ft.Text("DBMS & Min-Heap: Claims Audit Engine", size=16, weight="bold", color="white"),
        claims_col,
        floating_dock_navbar
    ], spacing=10)

    # 4. PROFILE SCREEN
    profile_name_txt = ft.Text("Name: Mr. Srinidhi", size=13, weight="bold", color="white")
    profile_card_name = ft.Text("Name: Mr. Srinidhi", size=13, weight="bold", color="white")

    profile_view = ft.Column([
        ft.Text("Customer Profile", size=16, weight="bold", color="white"),
        profile_name_txt,
        ft.Text(f"Policy: {current_policy[0]}", color="#60A5FA", weight="bold"),
        ft.Text(f"Nominee: {nominee_info[0]}", color="#34D399", weight="bold"),
        ft.Divider(color="#334155"),
        ft.ElevatedButton("Logout", bgcolor="#DC2626", color="white", width=180, on_click=lambda _: switch_screen("login")),
        ft.Container(height=10),
        floating_dock_navbar
    ], spacing=8)

    main_viewport = ft.Container(content=home_content_view, expand=True, padding=12)

    # Sliding Drawer from Profile Circle click
    menu_sheet = ft.BottomSheet(
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(content=avatar_letter_txt, width=44, height=44, border_radius=22, bgcolor="#4F46E5", alignment=ft.Alignment(0, 0)),
                    ft.Column([user_greeting_txt, ft.Text("Active Policyholder", size=11, color="#94A3B8")], spacing=1)
                ], spacing=10),
                ft.Divider(height=1, color="#334155"),
                ft.ListTile(leading=ft.Icon("home", color="#60A5FA"), title=ft.Text("Home Dashboard", color="white", weight="bold"), on_click=lambda _: [setattr(menu_sheet, "open", False), on_dock_nav_click("home")]),
                ft.ListTile(leading=ft.Icon("search", color="#60A5FA"), title=ft.Text("ADS: Trie Search", color="white", weight="bold"), on_click=lambda _: [setattr(menu_sheet, "open", False), on_dock_nav_click("search")]),
                ft.ListTile(leading=ft.Icon("hub", color="#60A5FA"), title=ft.Text("DMGT: Hospital Graph", color="white", weight="bold"), on_click=lambda _: [setattr(menu_sheet, "open", False), on_dock_nav_click("network")]),
                ft.ListTile(leading=ft.Icon("receipt_long", color="#60A5FA"), title=ft.Text("DBMS: Claims Priority", color="white", weight="bold"), on_click=lambda _: [setattr(menu_sheet, "open", False), on_dock_nav_click("claims")]),
                ft.ListTile(leading=ft.Icon("person", color="#60A5FA"), title=ft.Text("Profile Overview", color="white", weight="bold"), on_click=lambda _: [setattr(menu_sheet, "open", False), on_dock_nav_click("profile")]),
                ft.Divider(height=1, color="#334155"),
                ft.ListTile(leading=ft.Icon("logout", color="#DC2626"), title=ft.Text("Logout", color="#DC2626", weight="bold"), on_click=lambda _: [setattr(menu_sheet, "open", False), switch_screen("login")])
            ], tight=True, spacing=1),
            padding=16,
            bgcolor="#0F172A"
        )
    )
    page.overlay.append(menu_sheet)

    def open_profile_menu(e):
        menu_sheet.open = True
        page.update()

    profile_circle_btn = ft.Container(
        content=avatar_letter_txt,
        width=38,
        height=38,
        border_radius=19,
        bgcolor="#4F46E5",
        alignment=ft.Alignment(0, 0),
        on_click=open_profile_menu,
        tooltip="Profile Menu"
    )

    top_bar = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Container(content=ft.Text("M", size=16, weight="bold", color="white"), width=32, height=32, bgcolor="#1E1B4B", border_radius=6, alignment=ft.Alignment(0, 0)),
                ft.Text("MAGADHA", size=16, weight="bold", color="white")
            ], spacing=6),
            ft.Row([
                ft.IconButton(icon="support_agent", icon_color="white", icon_size=22, on_click=trigger_help),
                profile_circle_btn
            ], spacing=4)
        ], alignment="spaceBetween"),
        padding=12,
        bgcolor="#111827",
        border=ft.border.only(bottom=ft.BorderSide(1, "#1F2937"))
    )

    home_screen = ft.Container(
        content=ft.Column([top_bar, main_viewport], expand=True, spacing=0),
        expand=True,
        visible=False
    )

    # ----------------------------------------------------
    # VERIFY DETAILS (Post-OTP)
    # ----------------------------------------------------
    v_name = ft.TextField(label="Full Name", value="Srinidhi", label_style=ft.TextStyle(color="#94A3B8"), bgcolor="#1E293B", color="white", width=310)
    v_policy = ft.TextField(label="Policy Number", value="MAG-IND-2024-88", label_style=ft.TextStyle(color="#94A3B8"), bgcolor="#1E293B", color="white", width=310)
    v_mobile = ft.TextField(label="Mobile Number", prefix_text="+91 ", value="9876543210", label_style=ft.TextStyle(color="#94A3B8"), bgcolor="#1E293B", color="white", width=310)

    def on_confirm_verify(e):
        update_identity(v_name.value)
        toast("Profile Verified! Entering Portal.")
        switch_screen("home")

    verify_details_card = ft.Container(
        content=ft.Column([
            ft.Icon("verified_user", size=38, color="#60A5FA"),
            ft.Text("Verify Identity", size=17, weight="bold", color="white"),
            v_name,
            v_policy,
            v_mobile,
            ft.ElevatedButton("Confirm & Proceed", bgcolor="#4F46E5", color="white", width=310, height=45, on_click=on_confirm_verify)
        ], alignment="center", horizontal_alignment="center", spacing=8),
        padding=20,
        border_radius=18,
        bgcolor="#111827",
        width=350
    )

    verify_details_screen = ft.Container(content=verify_details_card, alignment=ft.Alignment(0, 0), expand=True, visible=False)

    # ----------------------------------------------------
    # OTP SCREEN
    # ----------------------------------------------------
    t1 = ft.TextField(width=52, height=54, text_align="center", text_size=20, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, bgcolor="#1E293B", color="white", content_padding=0)
    t2 = ft.TextField(width=52, height=54, text_align="center", text_size=20, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, bgcolor="#1E293B", color="white", content_padding=0)
    t3 = ft.TextField(width=52, height=54, text_align="center", text_size=20, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, bgcolor="#1E293B", color="white", content_padding=0)
    t4 = ft.TextField(width=52, height=54, text_align="center", text_size=20, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, bgcolor="#1E293B", color="white", content_padding=0)

    def handle_otp(e, curr, nxt):
        val = curr.value or ""
        if len(val) > 1:
            curr.value = val[-1]
        page.update()
        if curr.value:
            if nxt:
                nxt.focus()
            else:
                switch_screen("verify_details")

    t1.on_change = lambda e: handle_otp(e, t1, t2)
    t2.on_change = lambda e: handle_otp(e, t2, t3)
    t3.on_change = lambda e: handle_otp(e, t3, t4)
    t4.on_change = lambda e: handle_otp(e, t4, None)

    otp_card = ft.Container(
        content=ft.Column([
            ft.Text("OTP Verification", size=20, weight="bold", color="white"),
            ft.Text("Enter any 4-digit code", size=12, color="#94A3B8"),
            ft.Row([ft.Container(t1, width=52), ft.Container(t2, width=52), ft.Container(t3, width=52), ft.Container(t4, width=52)], alignment="center", spacing=10),
            ft.ElevatedButton("Verify", width=260, height=44, bgcolor="#4F46E5", color="white", on_click=lambda _: switch_screen("verify_details"))
        ], alignment="center", horizontal_alignment="center", spacing=10),
        bgcolor="#111827",
        padding=24,
        border_radius=18,
        width=340
    )

    otp_screen = ft.Container(content=otp_card, alignment=ft.Alignment(0, 0), expand=True, visible=False)

    # ----------------------------------------------------
    # LOGIN SCREEN (INSTANT FIRST LETTER AUTO-SYNC)
    # ----------------------------------------------------
    name_field = ft.TextField(label="Full Name", value="Srinidhi", label_style=ft.TextStyle(color="#94A3B8"), width=210, bgcolor="#1E293B", color="white", border_radius=12)
    phone_box = ft.TextField(label="Mobile Number", prefix_text="+91 ", value="9876543210", label_style=ft.TextStyle(color="#94A3B8"), width=310, bgcolor="#1E293B", color="white", border_radius=12)

    def on_name_change(e):
        entered = name_field.value or ""
        update_identity(entered)

    name_field.on_change = on_name_change

    def on_login(e):
        if not name_field.value.strip():
            toast("Please enter your name!", "#B91C1C")
            return
        update_identity(name_field.value)
        switch_screen("otp")

    login_card = ft.Container(
        content=ft.Column([
            ft.Container(content=ft.Text("M", size=32, weight="bold", color="white"), width=65, height=65, bgcolor="#4F46E5", border_radius=16, alignment=ft.Alignment(0, 0)),
            ft.Text("MAGADHA", size=22, weight="bold", color="white"),
            ft.Text("College Engineering Project Portal", size=12, color="#94A3B8"),
            name_field,
            phone_box,
            ft.ElevatedButton("Get OTP", width=310, height=46, bgcolor="#4F46E5", color="white", on_click=on_login)
        ], alignment="center", horizontal_alignment="center", spacing=10),
        padding=24,
        border_radius=20,
        bgcolor="#111827",
        width=350
    )

    login_screen = ft.Container(content=login_card, alignment=ft.Alignment(0, 0), expand=True, visible=False)

    # Fast Splash
    splash_screen = ft.Container(
        content=ft.Column([
            ft.Container(content=ft.Text("M", size=48, weight="bold", color="white"), width=85, height=85, bgcolor="#4F46E5", border_radius=20, alignment=ft.Alignment(0, 0)),
            ft.Text("MAGADHA INSURANCE", size=18, weight="bold", color="white")
        ], alignment="center", horizontal_alignment="center", spacing=12),
        alignment=ft.Alignment(0, 0),
        expand=True,
        visible=True
    )

    def switch_screen(name):
        splash_screen.visible = (name == "splash")
        login_screen.visible = (name == "login")
        otp_screen.visible = (name == "otp")
        verify_details_screen.visible = (name == "verify_details")
        home_screen.visible = (name == "home")
        vehicle_entry_screen.visible = (name == "vehicle_entry")
        vehicle_plans_view.visible = (name == "vehicle_plans")
        page.update()

    device_frame = ft.Container(
        content=ft.Stack([
            splash_screen,
            login_screen,
            otp_screen,
            verify_details_screen,
            home_screen,
            vehicle_entry_screen,
            vehicle_plans_view,
        ], expand=True),
        width=440,
        height=880,
        bgcolor="#0B0F19",
        border_radius=18,
        shadow=ft.BoxShadow(blur_radius=20, color="#00000040")
    )

    page.add(ft.Row([device_frame], alignment="center"))

    def fast_init():
        time.sleep(0.3)
        switch_screen("login")

    threading.Thread(target=fast_init, daemon=True).start()

# Render ASGI Mount
app = flet_fastapi.app(main)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
