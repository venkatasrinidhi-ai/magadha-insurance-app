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
# BACKEND ACADEMIC LOGIC (ADS, DMGT, DBMS - SILENTLY INTEGRATED)
# =====================================================================
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

class ClaimPriorityQueue:
    def __init__(self):
        self.heap = []
        self.counter = 0

    def push(self, priority, claim_id, data):
        heapq.heappush(self.heap, (priority, self.counter, claim_id, data))
        self.counter += 1

class HospitalNetworkGraph:
    def __init__(self):
        self.adj = {
            "Kakinada": ["Visakhapatnam", "Rajahmundry"],
            "Rajahmundry": ["Kakinada", "Vijayawada"],
            "Vijayawada": ["Rajahmundry", "Guntur", "Hyderabad"],
            "Hyderabad": ["Vijayawada"]
        }

    def get_hops(self, src, dst):
        if src not in self.adj or dst not in self.adj:
            return 1
        q = [(src, 0)]
        visited = {src}
        while q:
            cur, d = q.pop(0)
            if cur == dst:
                return d
            for n in self.adj.get(cur, []):
                if n not in visited:
                    visited.add(n)
                    q.append((n, d + 1))
        return 1

def dmgt_proposition_eval(policy_active, doc_verified, grace_period):
    return bool(policy_active and doc_verified and grace_period)

backend_trie = PolicyTrie()
backend_trie.insert("Car", {"cat": "Vehicle", "base": 3500})
backend_trie.insert("Bike", {"cat": "Vehicle", "base": 715})
backend_trie.insert("Home", {"cat": "Property", "base": 3200})

backend_pq = ClaimPriorityQueue()
backend_graph = HospitalNetworkGraph()

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
            FOREIGN KEY (policy_no) REFERENCES customer_profile(policy_no)
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
            FOREIGN KEY (policy_no) REFERENCES customer_profile(policy_no)
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
    months_data = [
        (f"TXN-{100+i}", "MAG-IND-2024-88", "Monthly Twin Shield", f"2025-{i:02d}-15" if i <= 12 else f"2026-{i-12:02d}-15", "Rs. 1,250", "Success")
        for i in range(1, 15)
    ]
    c.executemany("INSERT OR IGNORE INTO payment_history VALUES (?, ?, ?, ?, ?, ?)", months_data)
    c.execute("INSERT OR IGNORE INTO claims VALUES ('CLM-1001', 'MAG-IND-2024-88', 'Health', 'ICU Hospitalization', 'Rs. 45,000', 1, '2026-02-10', 'Approved')")
    conn.commit()
    conn.close()

init_db()

def get_pure_initial(name_val):
    if not name_val:
        return "U"
    cleaned = "".join([c for c in name_val if c.isalpha()])
    return cleaned[0].upper() if len(cleaned) > 0 else "U"

def main(page: ft.Page):
    page.title = "Magadha Life & Health Insurance"
    page.padding = 0
    page.bgcolor = "#0B0F19"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "start"

    user_name = ["Srinidhi"]
    user_salutation = ["Mr."]
    current_policy = ["MAG-IND-2024-88"]
    current_mobile = ["9876543210"]
    current_aadhaar = ["XXXX-XXXX-7892"]
    nominee_info = ["Family Nominee"]
    eye_open = [False]
    card_side = ["life"]
    terms_checked = [False]

    def toast(msg, color="#1E1B4B"):
        snack = ft.SnackBar(ft.Text(msg, color="white", weight="bold"), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    avatar_letter_txt = ft.Text("S", size=18, weight="bold", color="white")
    user_greeting_txt = ft.Text("Hi Srinidhi", size=17, weight="bold", color="#0F172A")
    card_holder_name_txt = ft.Text("SRINIDHI", size=11, weight="bold", color="white")

    def sync_user_data(new_name):
        c_name = new_name.strip()
        if c_name:
            user_name[0] = c_name
            init_letter = get_pure_initial(c_name)
            avatar_letter_txt.value = init_letter
            user_greeting_txt.value = f"Hi {c_name}"
            card_holder_name_txt.value = c_name.upper()
            profile_name_txt.value = f"Name: {user_salutation[0]} {c_name}"
            p3_name.value = c_name
        page.update()

    # ----------------------------------------------------
    # ENGLISH AI ASSISTANT CHAT
    # ----------------------------------------------------
    help_chat_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=270, auto_scroll=True)
    help_input = ft.TextField(hint_text="Ask about policies, claims, terms...", text_size=12, expand=True, bgcolor="#F8FAFC", border_color="#CBD5E1", color="#0F172A")

    def make_bubble(txt, is_user=False):
        return ft.Row(
            [
                ft.Container(
                    content=ft.Text(txt, color="white" if is_user else "#0F172A", size=12, no_wrap=False),
                    bgcolor="#4F46E5" if is_user else "#E2E8F0",
                    padding=10,
                    border_radius=12,
                    width=270
                )
            ],
            alignment="end" if is_user else "start"
        )

    def resolve_help(query):
        q = query.lower().strip()
        if q in ["hi", "hello", "hey", "help"]:
            return f"Hello {user_name[0]}! I am Magadha AI Support. How can I assist you with your policies or claims today?"
        elif "claim" in q:
            return "Tap 'Life Claim' or 'Health Claim' on Home. Our priority triage engine processes claims within 4 business hours."
        elif "policy" in q:
            return f"Your active schedule {current_policy[0]} provides Rs. 15,00,000 cashless cover valid until 14 Jan 2027."
        elif "card" in q or "flip" in q:
            return "Tap your virtual pass on Home to flip horizontally between Life and Health cashless passes."
        else:
            return f"Regarding '{query}', all settlements and policy updates are handled instantly. Call 1800-MAGADHA for phone support."

    def on_send_help(e):
        msg = help_input.value.strip()
        if not msg:
            return
        help_chat_col.controls.append(make_bubble(msg, is_user=True))
        help_input.value = ""
        page.update()
        ans = resolve_help(msg)
        time.sleep(0.2)
        help_chat_col.controls.append(make_bubble(ans, is_user=False))
        page.update()

    help_chat_col.controls.append(make_bubble("Hello! I am Magadha Help Desk. Ask me any question in English.", is_user=False))

    help_sheet = ft.BottomSheet(
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([ft.Icon("support_agent", color="#4F46E5", size=24), ft.Text("Magadha Help Desk", size=15, weight="bold", color="#0F172A")]),
                    ft.IconButton(icon="close", icon_size=18, on_click=lambda _: setattr(help_sheet, "open", False) or page.update())
                ], alignment="spaceBetween"),
                ft.Divider(height=1),
                help_chat_col,
                ft.Row([help_input, ft.IconButton(icon="send", icon_color="#4F46E5", on_click=on_send_help)], spacing=4)
            ], tight=True, spacing=6),
            padding=16,
            bgcolor="white",
            width=390
        )
    )
    page.overlay.append(help_sheet)

    def trigger_help(e):
        help_sheet.open = True
        page.update()

    floating_help_pill = ft.Container(
        content=ft.Row([
            ft.Icon("headset_mic", color="white", size=13),
            ft.Text("NEED HELP?", size=10, weight="bold", color="white")
        ], spacing=4, alignment="center"),
        bgcolor="#2563EB",
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        border_radius=20,
        on_click=trigger_help
    )

    # ----------------------------------------------------
    # REFERENCE VIDEO: DOCK/PILL NAVBAR MENU POPUP
    # ----------------------------------------------------
    nav_item_active = ["home"]

    def make_nav_dock_button(label, icon_name, target_id):
        is_active = (nav_item_active[0] == target_id)
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon_name, color="#60A5FA" if is_active else "#94A3B8", size=17),
                ft.Text(label, color="white" if is_active else "#94A3B8", size=12, weight="bold" if is_active else "normal")
            ], spacing=6),
            bgcolor="#1E293B" if is_active else "#00000000",
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=20,
            border=ft.border.all(1, "#3B82F6") if is_active else None,
            on_click=lambda _: on_select_nav_dock(target_id)
        )

    def build_dock_row():
        return ft.Container(
            content=ft.Row([
                make_nav_dock_button("Home", "home", "home"),
                make_nav_dock_button("Claims", "receipt_long", "claims"),
                make_nav_dock_button("Explore", "storefront", "explore"),
                make_nav_dock_button("History", "history", "history"),
                make_nav_dock_button("Profile", "person", "profile"),
            ], alignment="center", spacing=4, scroll=ft.ScrollMode.ADAPTIVE),
            bgcolor="#0F172A",
            padding=8,
            border_radius=25,
            border=ft.border.all(1.5, "#334155"),
            shadow=ft.BoxShadow(blur_radius=15, color="#00000080")
        )

    nav_dock_container = build_dock_row()

    def on_select_nav_dock(tab_id):
        nav_item_active[0] = tab_id
        nav_dock_container.content = build_dock_row().content
        profile_menu_sheet.open = False
        if tab_id == "home":
            main_viewport.content = home_content_view
        elif tab_id == "claims":
            main_viewport.content = claims_view
        elif tab_id == "explore":
            main_viewport.content = explore_view
        elif tab_id == "history":
            main_viewport.content = history_view
        elif tab_id == "profile":
            main_viewport.content = profile_view
        page.update()

    profile_menu_sheet = ft.BottomSheet(
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(content=avatar_letter_txt, width=44, height=44, border_radius=22, bgcolor="#4F46E5", alignment=ft.Alignment(0, 0)),
                    ft.Column([user_greeting_txt, ft.Text("Active Policyholder", size=11, color="#64748B", weight="bold")], spacing=1)
                ], spacing=10),
                ft.Divider(height=1),
                nav_dock_container,
                ft.Divider(height=1),
                ft.ListTile(leading=ft.Icon("logout", color="#DC2626"), title=ft.Text("Logout Account", color="#DC2626", weight="bold"), on_click=lambda _: [setattr(profile_menu_sheet, "open", False), switch_screen("page1")]),
            ], tight=True, spacing=10),
            padding=16,
            bgcolor="white"
        )
    )
    page.overlay.append(profile_menu_sheet)

    def open_profile_menu(e):
        profile_menu_sheet.open = True
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

    # ----------------------------------------------------
    # PAGE 5: VIRTUAL CARD (3D HORIZONTAL ROTATE)
    # ----------------------------------------------------
    life_card_content = ft.Column([
        ft.Row([
            ft.Row([ft.Icon("shield", color="#FBBF24", size=18), ft.Text("LIFE INSURANCE PASS", size=11, weight="bold", color="white")], spacing=4),
            ft.Container(content=ft.Row([ft.Icon("rotate_right", size=11, color="white"), ft.Text("Flip Card", size=9, color="white", weight="bold")], spacing=2), bgcolor="#FFFFFF26", padding=4, border_radius=4)
        ], alignment="spaceBetween"),
        ft.Container(height=2),
        ft.Row([ft.Container(width=34, height=22, bgcolor="#F59E0B", border_radius=4), ft.Icon("contactless", color="white", size=18)], alignment="spaceBetween"),
        ft.Container(height=4),
        ft.Text("5412  8801  9924  7710", size=14, weight="bold", color="white", font_family="monospace"),
        ft.Row([
            ft.Column([ft.Text("INSURED MEMBER", size=8, color="#CBD5E1", weight="bold"), card_holder_name_txt], spacing=1),
            ft.Column([ft.Text("COVERAGE", size=8, color="#CBD5E1", weight="bold"), ft.Text("Rs. 15 LAKHS", size=11, weight="bold", color="#38BDF8")], spacing=1),
            ft.Container(content=ft.Text("NOMINEE PROT", size=9, weight="bold", color="#FBBF24"), bgcolor="#451A03", padding=4, border_radius=4)
        ], alignment="spaceBetween")
    ], spacing=3)

    health_card_content = ft.Column([
        ft.Row([
            ft.Row([ft.Icon("local_hospital", color="#34D399", size=18), ft.Text("HEALTH CASHLESS PASS", size=11, weight="bold", color="white")], spacing=4),
            ft.Container(content=ft.Row([ft.Icon("rotate_right", size=11, color="white"), ft.Text("Flip Card", size=9, color="white", weight="bold")], spacing=2), bgcolor="#FFFFFF26", padding=4, border_radius=4)
        ], alignment="spaceBetween"),
        ft.Container(height=2),
        ft.Row([ft.Container(width=34, height=22, bgcolor="#10B981", border_radius=4), ft.Icon("wifi", color="white", size=18)], alignment="spaceBetween"),
        ft.Container(height=4),
        ft.Text("4532  6612  3341  8821", size=14, weight="bold", color="white", font_family="monospace"),
        ft.Row([
            ft.Column([ft.Text("PRIMARY HOLDER", size=8, color="#E2E8F0", weight="bold"), card_holder_name_txt], spacing=1),
            ft.Column([ft.Text("FAMILY COVER", size=8, color="#E2E8F0", weight="bold"), ft.Text("4 MEMBERS", size=11, weight="bold", color="#FDE047")], spacing=1),
            ft.Container(content=ft.Text("CASHLESS", size=9, weight="bold", color="#064E3B"), bgcolor="#A7F3D0", padding=4, border_radius=4)
        ], alignment="spaceBetween")
    ], spacing=3)

    virtual_card_container = ft.Container(
        content=life_card_content,
        width=380,
        height=165,
        padding=14,
        border_radius=16,
        bgcolor="#0F172A",
        shadow=ft.BoxShadow(blur_radius=12, color="#02061730"),
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
    eye_btn = ft.IconButton(icon="visibility_off", icon_color="#1E1B4B", icon_size=18)

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
            ft.Text("Death Reason Payout Breakdown:", size=11, weight="bold", color="#0F172A"),
            ft.Row([ft.Text("• Natural Death: Rs. 15,00,000", size=10, color="#1E293B", weight="bold"), ft.Text("• Accident: Rs. 30,00,000", size=10, color="#047857", weight="bold")], alignment="spaceBetween"),
            ft.Text("• Critical Illness: Rs. 20,00,000", size=10, color="#B91C1C", weight="bold"),
            ft.Container(
                content=ft.Row([ft.Icon("assignment_ind", size=13, color="#1E1B4B"), ft.Text(f"Nominee Guaranteed: {nominee_info[0]} settlement assured.", size=9, weight="bold", color="#1E1B4B")], spacing=4),
                bgcolor="#E0E7FF",
                padding=4,
                border_radius=4
            )
        ], spacing=4),
        padding=12,
        border_radius=14,
        bgcolor="#FFFFFF",
        border=ft.border.all(1.5, "#94A3B8")
    )

    action_buttons = ft.Row([
        ft.ElevatedButton("Life Claim", icon="family_restroom", bgcolor="#312E81", color="white", height=42, expand=True, on_click=lambda _: toast("Submitted to Min-Heap Priority Queue!")),
        ft.ElevatedButton("Health Claim", icon="local_hospital", bgcolor="#047857", color="white", height=42, expand=True, on_click=lambda _: toast("Submitted to Min-Heap Priority Queue!"))
    ], spacing=8)

    big_car_card = ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Container(content=ft.Text("UP TO 85% OFF", size=9, weight="bold", color="white"), bgcolor="#2563EB", padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4),
                ft.Text("Car Insurance", size=15, weight="bold", color="white"),
                ft.Text("Cashless repairs in 6500+ garages", size=10, color="#94A3B8"),
                ft.Container(height=2),
                ft.ElevatedButton("Get Quotes", bgcolor="white", color="#1E1B4B", height=30, on_click=lambda _: toast("Vehicle Insurance Quotes Loaded!"))
            ], spacing=2, expand=True),
            ft.Icon("directions_car_filled", size=55, color="#60A5FA")
        ], alignment="spaceBetween"),
        padding=14,
        border_radius=16,
        bgcolor="#1E1B4B",
        on_click=lambda _: toast("Opening Vehicle Insurance Quotes...")
    )

    big_bike_card = ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Container(content=ft.Text("INSTANT POLICY IN 2 MINS", size=9, weight="bold", color="white"), bgcolor="#059669", padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4),
                ft.Text("Two Wheeler Insurance", size=15, weight="bold", color="white"),
                ft.Text("Starting @ just ₹715/year", size=10, color="#A7F3D0"),
                ft.Container(height=2),
                ft.ElevatedButton("View Plans", bgcolor="white", color="#064E3B", height=30, on_click=lambda _: toast("Two-Wheeler Policy Ready!"))
            ], spacing=2, expand=True),
            ft.Icon("two_wheeler", size=55, color="#34D399")
        ], alignment="spaceBetween"),
        padding=14,
        border_radius=16,
        bgcolor="#064E3B",
        on_click=lambda _: toast("Opening Two-Wheeler Plans...")
    )

    other_categories_grid = ft.Row([
        ft.Container(content=ft.Column([ft.Icon("home", color="#D97706", size=22), ft.Text("Home", size=10, weight="bold", color="#0F172A")], horizontal_alignment="center", spacing=3), bgcolor="white", padding=8, border_radius=12, expand=True, on_click=lambda _: toast("Home Shield Active")),
        ft.Container(content=ft.Column([ft.Icon("store", color="#7C3AED", size=22), ft.Text("Business", size=10, weight="bold", color="#0F172A")], horizontal_alignment="center", spacing=3), bgcolor="white", padding=8, border_radius=12, expand=True, on_click=lambda _: toast("Business Shield Active")),
        ft.Container(content=ft.Column([ft.Icon("flight_takeoff", color="#0891B2", size=22), ft.Text("Travel", size=10, weight="bold", color="#0F172A")], horizontal_alignment="center", spacing=3), bgcolor="white", padding=8, border_radius=12, expand=True, on_click=lambda _: toast("Travel Cover Active")),
        ft.Container(content=ft.Column([ft.Icon("lock", color="#DC2626", size=22), ft.Text("Cyber", size=10, weight="bold", color="#0F172A")], horizontal_alignment="center", spacing=3), bgcolor="white", padding=8, border_radius=12, expand=True, on_click=lambda _: toast("Cyber Fraud Protection Active"))
    ], spacing=6)

    # ----------------------------------------------------
    # ORIGINAL HOME VIEW LAYOUT
    # ----------------------------------------------------
    home_content_view = ft.Column([
        user_greeting_txt,
        virtual_card_container,
        coverage_detail_box,
        action_buttons,
        ft.Container(height=4),
        ft.Row([ft.Text("Vehicle Protection", size=14, weight="bold", color="#0F172A"), ft.Text("Best Quotes", size=11, weight="bold", color="#2563EB")], alignment="spaceBetween"),
        big_car_card,
        big_bike_card,
        ft.Container(height=2),
        ft.Text("More Insurance Products", size=13, weight="bold", color="#0F172A"),
        other_categories_grid,
        ft.Container(height=4),
        ft.Text("Live fulfilled", size=15, weight="bold", color="#1E293B", italic=True, text_align="center"),
        ft.Text("Instant cashless access & Nominee security", size=11, color="#64748B", text_align="center"),
        ft.Container(height=2),
        ft.Row([
            ft.Column([ft.Text("Magadha 24x7 Assistance", size=11, weight="bold", color="#0F172A"), ft.Text("Need instant claims or policy support?", size=10, color="#64748B")], spacing=1),
            floating_help_pill
        ], alignment="spaceBetween"),
        ft.Container(height=20)
    ], horizontal_alignment="center", spacing=10, scroll=ft.ScrollMode.AUTO)

    profile_name_txt = ft.Text("Name: Mr. Srinidhi", size=13, weight="bold", color="#0F172A")
    profile_view = ft.Column([
        ft.Text("Customer Profile", size=16, weight="bold", color="#0F172A"),
        profile_name_txt,
        ft.Text(f"Policy: {current_policy[0]}", color="#4F46E5", weight="bold"),
        ft.Text(f"Nominee: {nominee_info[0]}", color="#059669", weight="bold"),
        ft.Divider(),
        ft.ElevatedButton("Logout", bgcolor="#FEE2E2", color="#DC2626", width=180, on_click=lambda _: switch_screen("page1")),
    ], spacing=10)

    claims_view = ft.Column([ft.Text("Claims Center (Min-Heap Prioritized)", size=16, weight="bold", color="#0F172A"), coverage_detail_box, action_buttons], spacing=10)
    explore_view = ft.Column([ft.Text("Explore Insurance", size=16, weight="bold", color="#0F172A"), big_car_card, big_bike_card, other_categories_grid], spacing=10)
    history_view = ft.Column([ft.Text("Payment History (DBMS Relational)", size=16, weight="bold", color="#0F172A"), coverage_detail_box], spacing=10)

    main_viewport = ft.Container(content=home_content_view, expand=True, padding=12)

    top_bar = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Container(content=ft.Text("M", size=16, weight="bold", color="white"), width=32, height=32, bgcolor="#1E1B4B", border_radius=6, alignment=ft.Alignment(0, 0)),
                ft.Text("MAGADHA", size=16, weight="bold", color="#0F172A")
            ], spacing=6),
            ft.Row([
                ft.TextButton(
                    content=ft.Row([ft.Icon("call", size=14, color="#1E1B4B"), ft.Text("1800-MAGADHA", size=11, weight="bold", color="#1E1B4B")], spacing=2),
                    on_click=lambda _: toast("Dialing Toll-Free: 1800-MAGADHA")
                ),
                profile_circle_btn
            ], spacing=4)
        ], alignment="spaceBetween"),
        padding=12,
        bgcolor="white",
        border=ft.border.only(bottom=ft.BorderSide(1, "#CBD5E1"))
    )

    page5_home = ft.Container(
        content=ft.Column([top_bar, main_viewport], expand=True, spacing=0),
        expand=True,
        visible=False
    )

    # ----------------------------------------------------
    # PAGE 4: TERMS & CONDITIONS (EMPTY BOX CLICK TO TICK)
    # ----------------------------------------------------
    t_checkbox_icon = ft.Icon("check_box_outline_blank", size=24, color="#64748B")
    login_portal_btn = ft.ElevatedButton("Login & Enter Portal", width=310, height=48, bgcolor="#CBD5E1", color="#94A3B8", disabled=True)

    def on_toggle_terms(e):
        terms_checked[0] = not terms_checked[0]
        if terms_checked[0]:
            t_checkbox_icon.name = "check_box"
            t_checkbox_icon.color = "#4F46E5"
            login_portal_btn.bgcolor = "#1E1B4B"
            login_portal_btn.color = "white"
            login_portal_btn.disabled = False
        else:
            t_checkbox_icon.name = "check_box_outline_blank"
            t_checkbox_icon.color = "#64748B"
            login_portal_btn.bgcolor = "#CBD5E1"
            login_portal_btn.color = "#94A3B8"
            login_portal_btn.disabled = True
        page.update()

    def on_final_login_click(e):
        toast(f"Welcome {user_name[0]}! Unlocking Portal.", "#047857")
        switch_screen("page5")

    login_portal_btn.on_click = on_final_login_click

    page4_terms = ft.Container(
        content=ft.Container(
            content=ft.Column([
                ft.Icon("gavel", size=40, color="#1E1B4B"),
                ft.Text("Terms & Conditions", size=18, weight="bold", color="#0F172A"),
                ft.Container(
                    content=ft.Column([
                        ft.Text("1. Policy Benefits: Guaranteed settlement for designated nominees.", size=11, color="#334155", weight="w500"),
                        ft.Text("2. Cashless Admission: 6,500+ networked hospitals nationwide.", size=11, color="#334155", weight="w500"),
                        ft.Text("3. Data Privacy: 256-bit encryption compliant with IRDAI rules.", size=11, color="#334155", weight="w500"),
                        ft.Text("4. Claims: Emergency requests audited via Priority Queues.", size=11, color="#334155", weight="w500"),
                    ], spacing=6),
                    bgcolor="#F8FAFC",
                    padding=14,
                    border_radius=10,
                    border=ft.border.all(1, "#E2E8F0")
                ),
                ft.Container(height=6),
                ft.GestureDetector(
                    content=ft.Row([
                        t_checkbox_icon,
                        ft.Text("I agree to all policy terms and IRDAI rules", size=12, weight="bold", color="#0F172A")
                    ], spacing=8),
                    on_tap=on_toggle_terms
                ),
                ft.Container(height=10),
                login_portal_btn
            ], alignment="center", horizontal_alignment="center", spacing=10),
            padding=24,
            border_radius=18,
            border=ft.border.all(1.5, "#CBD5E1"),
            bgcolor="white",
            width=360
        ),
        alignment=ft.Alignment(0, 0),
        expand=True,
        visible=False
    )

    # ----------------------------------------------------
    # PAGE 3: POLICY CUSTOMER DETAILS
    # ----------------------------------------------------
    p3_name = ft.TextField(label="Customer Full Name", label_style=ft.TextStyle(color="#0F172A", weight="bold"), bgcolor="#F8FAFC", border_color="#475569", color="#0F172A", text_size=14, width=310)
    p3_policy = ft.TextField(label="Policy Number", label_style=ft.TextStyle(color="#0F172A", weight="bold"), value="MAG-IND-2024-88", bgcolor="#F8FAFC", border_color="#475569", color="#0F172A", text_size=14, width=310)
    p3_aadhaar = ft.TextField(label="Aadhaar Number", label_style=ft.TextStyle(color="#0F172A", weight="bold"), value="XXXX-XXXX-7892", bgcolor="#F8FAFC", border_color="#475569", color="#0F172A", text_size=14, width=310)
    p3_mobile = ft.TextField(label="Mobile Number", prefix_text="+91 ", label_style=ft.TextStyle(color="#0F172A", weight="bold"), value="9876543210", bgcolor="#F8FAFC", border_color="#475569", color="#0F172A", text_size=14, width=310)

    def on_p3_continue(e):
        if not p3_name.value.strip() or not p3_mobile.value.strip():
            toast("Please enter all details!", "#B91C1C")
            return
        sync_user_data(p3_name.value)
        switch_screen("page4")

    page3_policy_details = ft.Container(
        content=ft.Container(
            content=ft.Column([
                ft.Icon("verified_user", size=38, color="#1E1B4B"),
                ft.Text("Customer Policy Schedule", size=18, weight="bold", color="#0F172A"),
                ft.Text("Confirm your registered identity details", size=11, color="#64748B"),
                p3_name,
                p3_policy,
                p3_aadhaar,
                p3_mobile,
                ft.Container(height=4),
                ft.ElevatedButton("Continue", width=310, height=46, bgcolor="#1E1B4B", color="white", on_click=on_p3_continue)
            ], alignment="center", horizontal_alignment="center", spacing=8),
            padding=20,
            border_radius=18,
            border=ft.border.all(1.5, "#CBD5E1"),
            bgcolor="white",
            width=350
        ),
        alignment=ft.Alignment(0, 0),
        expand=True,
        visible=False
    )

    # ----------------------------------------------------
    # PAGE 2: OTP (NUMBERS UP + ROTATING CIRCLE + TICK)
    # ----------------------------------------------------
    ot1 = ft.TextField(width=52, height=54, text_align="center", text_size=20, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, bgcolor="#F8FAFC", border_color="#475569", color="#0F172A", content_padding=0)
    ot2 = ft.TextField(width=52, height=54, text_align="center", text_size=20, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, bgcolor="#F8FAFC", border_color="#475569", color="#0F172A", content_padding=0)
    ot3 = ft.TextField(width=52, height=54, text_align="center", text_size=20, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, bgcolor="#F8FAFC", border_color="#475569", color="#0F172A", content_padding=0)
    ot4 = ft.TextField(width=52, height=54, text_align="center", text_size=20, keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, bgcolor="#F8FAFC", border_color="#475569", color="#0F172A", content_padding=0)

    otp_row_box = ft.Container(
        content=ft.Row([
            ft.Container(content=ot1, width=52, height=54, clip_behavior=ft.ClipBehavior.HARD_EDGE),
            ft.Container(content=ot2, width=52, height=54, clip_behavior=ft.ClipBehavior.HARD_EDGE),
            ft.Container(content=ot3, width=52, height=54, clip_behavior=ft.ClipBehavior.HARD_EDGE),
            ft.Container(content=ot4, width=52, height=54, clip_behavior=ft.ClipBehavior.HARD_EDGE),
        ], alignment="center", spacing=10),
        animate_offset=ft.Animation(400, "easeOut"),
        offset=ft.transform.Offset(0, 0)
    )

    rotating_loader = ft.ProgressRing(width=48, height=48, stroke_width=4, color="#4F46E5", visible=False)
    green_tick = ft.Container(
        content=ft.Icon("check", size=36, color="white"),
        width=58,
        height=58,
        border_radius=29,
        bgcolor="#059669",
        alignment=ft.Alignment(0, 0),
        scale=0.1,
        opacity=0.0,
        animate_scale=ft.Animation(500, "elasticOut"),
        animate_opacity=ft.Animation(300, "easeIn"),
        visible=False
    )

    otp_status_lbl = ft.Text("Enter any 4-digit code sent to mobile", size=12, color="#0F172A", weight="bold", text_align="center")

    def run_otp_success_animation():
        otp_row_box.offset = ft.transform.Offset(0, -0.2)
        rotating_loader.visible = True
        page.update()
        time.sleep(0.4)

        rotating_loader.visible = False
        otp_row_box.visible = False
        green_tick.visible = True
        green_tick.scale = 1.0
        green_tick.opacity = 1.0
        otp_status_lbl.value = "OTP Verified Successfully!"
        otp_status_lbl.color = "#059669"
        page.update()

        time.sleep(0.7)
        switch_screen("page3")

    def handle_otp_step(e, curr, nxt):
        val = curr.value or ""
        if len(val) > 1:
            curr.value = val[-1]
        page.update()
        if curr.value:
            if nxt:
                nxt.focus()
            else:
                code = f"{ot1.value or ''}{ot2.value or ''}{ot3.value or ''}{ot4.value or ''}".strip()
                if len(code) == 4:
                    run_otp_success_animation()

    ot1.on_change = lambda e: handle_otp_step(e, ot1, ot2)
    ot2.on_change = lambda e: handle_otp_step(e, ot2, ot3)
    ot3.on_change = lambda e: handle_otp_step(e, ot3, ot4)
    ot4.on_change = lambda e: handle_otp_step(e, ot4, None)

    page2_otp = ft.Container(
        content=ft.Container(
            content=ft.Column([
                ft.Text("OTP Verification", size=20, weight="bold", color="#0F172A"),
                otp_status_lbl,
                ft.Container(height=10),
                ft.Stack([
                    otp_row_box,
                    ft.Container(content=rotating_loader, alignment=ft.Alignment(0, 0), height=58),
                    ft.Container(content=green_tick, alignment=ft.Alignment(0, 0), height=58)
                ], alignment=ft.Alignment(0, 0)),
                ft.Container(height=16),
                ft.ElevatedButton("Verify & Continue", width=280, height=46, bgcolor="#1E1B4B", color="white", on_click=lambda _: run_otp_success_animation()),
                ft.TextButton("Change Mobile Number", on_click=lambda _: switch_screen("page1"))
            ], alignment="center", horizontal_alignment="center", spacing=10),
            bgcolor="white",
            padding=24,
            border_radius=18,
            border=ft.border.all(1.5, "#CBD5E1"),
            width=350
        ),
        alignment=ft.Alignment(0, 0),
        expand=True,
        visible=False
    )

    # ----------------------------------------------------
    # PAGE 1: LOGIN (MR/MS, NAME, MOBILE)
    # ----------------------------------------------------
    title_dropdown = ft.Dropdown(
        label="Title",
        label_style=ft.TextStyle(color="#0F172A", weight="bold"),
        width=90,
        options=[ft.dropdown.Option("Mr."), ft.dropdown.Option("Mrs."), ft.dropdown.Option("Ms.")],
        value="Mr.",
        bgcolor="#F8FAFC",
        border_color="#475569",
        color="#0F172A",
        border_radius=12
    )

    def on_name_type_sync(e):
        val = (login_name_field.value or "").strip()
        if val:
            sync_user_data(val)

    login_name_field = ft.TextField(
        label="Full Name",
        label_style=ft.TextStyle(color="#0F172A", weight="bold"),
        value="Srinidhi",
        hint_text="Enter your full name",
        width=210,
        bgcolor="#F8FAFC",
        border_color="#475569",
        color="#0F172A",
        border_radius=12,
        on_change=on_name_type_sync
    )

    login_phone_box = ft.TextField(
        label="Mobile Number",
        label_style=ft.TextStyle(color="#0F172A", weight="bold"),
        prefix=ft.Text("+91 ", size=14, weight="bold", color="#0F172A"),
        value="9876543210",
        keyboard_type=ft.KeyboardType.PHONE,
        width=310,
        bgcolor="#F8FAFC",
        border_color="#475569",
        color="#0F172A",
        border_radius=12
    )

    def show_permissions_dialog():
        def on_grant(e):
            page.dialog.open = False
            sync_user_data(login_name_field.value)
            switch_screen("page2")

        page.dialog = ft.AlertDialog(
            bgcolor="#0F172A",
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Row([ft.Icon("security", color="#60A5FA", size=20), ft.Text("App Permissions", size=16, weight="bold", color="white")], spacing=6),
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(leading=ft.Icon("camera_alt", color="#60A5FA", size=22), title=ft.Text("Camera Permission", size=12, weight="bold", color="white"), subtitle=ft.Text("Instant document scans", size=10, color="#CBD5E1")),
                    ft.ListTile(leading=ft.Icon("folder", color="#60A5FA", size=22), title=ft.Text("Storage Permission", size=12, weight="bold", color="white"), subtitle=ft.Text("Claim invoices & policy docs", size=10, color="#CBD5E1")),
                    ft.ListTile(leading=ft.Icon("sms", color="#60A5FA", size=22), title=ft.Text("SMS Access", size=12, weight="bold", color="white"), subtitle=ft.Text("Instant OTP verification", size=10, color="#CBD5E1")),
                ], tight=True, spacing=2),
                width=300
            ),
            actions=[
                ft.TextButton(content=ft.Text("Deny", size=12, weight="bold", color="#94A3B8"), on_click=lambda _: setattr(page.dialog, "open", False) or page.update()),
                ft.ElevatedButton("Allow & Continue", bgcolor="#4F46E5", color="white", on_click=on_grant)
            ]
        )
        page.dialog.open = True
        page.update()

    def on_get_otp(e):
        n_val = login_name_field.value.strip()
        m_val = login_phone_box.value.strip()
        if not n_val:
            toast("Please enter your name!", "#B91C1C")
            return
        if len(m_val) == 10 and m_val.isdigit():
            user_salutation[0] = title_dropdown.value or "Mr."
            current_mobile[0] = m_val
            p3_mobile.value = m_val
            show_permissions_dialog()
        else:
            toast("Enter valid 10-digit mobile number!", "#B91C1C")

    page1_login = ft.Container(
        content=ft.Container(
            content=ft.Column([
                ft.Container(content=ft.Text("M", size=32, weight="bold", color="white"), width=65, height=65, bgcolor="#1E1B4B", border_radius=16, alignment=ft.Alignment(0, 0)),
                ft.Text("MAGADHA", size=22, weight="bold", color="#0F172A"),
                ft.Text("Life & Health Insurance Portal", size=12, color="#334155", weight="bold"),
                ft.Container(height=4),
                ft.Row([title_dropdown, login_name_field], width=310, spacing=10),
                login_phone_box,
                ft.ElevatedButton("Get OTP", width=310, height=46, bgcolor="#1E1B4B", color="white", on_click=on_get_otp)
            ], alignment="center", horizontal_alignment="center", spacing=10),
            padding=24,
            border_radius=20,
            border=ft.border.all(1.5, "#CBD5E1"),
            bgcolor="white",
            width=350
        ),
        alignment=ft.Alignment(0, 0),
        expand=True,
        visible=True
    )

    def switch_screen(target_name):
        page1_login.visible = (target_name == "page1")
        page2_otp.visible = (target_name == "page2")
        page3_policy_details.visible = (target_name == "page3")
        page4_terms.visible = (target_name == "page4")
        page5_home.visible = (target_name == "page5")

        if target_name == "page2":
            ot1.value = ""
            ot2.value = ""
            ot3.value = ""
            ot4.value = ""
            otp_row_box.visible = True
            otp_row_box.offset = ft.transform.Offset(0, 0)
            rotating_loader.visible = False
            green_tick.visible = False
            green_tick.scale = 0.1
            green_tick.opacity = 0.0
            otp_status_lbl.value = f"Enter code sent to +91 {current_mobile[0]}"
            otp_status_lbl.color = "#0F172A"
            ot1.focus()

        page.update()

    device_frame = ft.Container(
        content=ft.Stack([
            page1_login,
            page2_otp,
            page3_policy_details,
            page4_terms,
            page5_home
        ], expand=True),
        width=440,
        height=880,
        bgcolor="#F8FAFC",
        border_radius=18,
        shadow=ft.BoxShadow(blur_radius=20, color="#00000040")
    )

    page.add(ft.Row([device_frame], alignment="center"))

    sync_user_data(login_name_field.value)

# Render ASGI Web Server Mount
app = flet_fastapi.app(main)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
