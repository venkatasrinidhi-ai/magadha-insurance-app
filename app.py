import flet as ft
import flet.fastapi as flet_fastapi
import sqlite3
import datetime
import threading
import time
import math
import os

DB_FILE = "magadha_insurance.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS customer_profile (
            policy_no TEXT PRIMARY KEY,
            full_name TEXT,
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
    
    c.execute("PRAGMA table_info(customer_profile)")
    columns = [row[1] for row in c.fetchall()]
    if "nominee_name" not in columns:
        c.execute("ALTER TABLE customer_profile ADD COLUMN nominee_name TEXT DEFAULT 'Sita Devi'")
    if "nominee_relation" not in columns:
        c.execute("ALTER TABLE customer_profile ADD COLUMN nominee_relation TEXT DEFAULT 'Spouse'")

    c.execute("""
        CREATE TABLE IF NOT EXISTS payment_history (
            txn_id TEXT PRIMARY KEY,
            policy_no TEXT,
            month_paid TEXT,
            payment_date TEXT,
            amount_paid TEXT,
            status TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY,
            policy_no TEXT,
            claim_type TEXT,
            incident_type TEXT,
            claim_amt TEXT,
            claim_date TEXT,
            status TEXT
        )
    """)
    
    c.execute("""
        INSERT OR REPLACE INTO customer_profile VALUES (
            'MAG-IND-2024-88',
            'User',
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
        (f"TXN-{100+i}", "MAG-IND-2024-88", f"Month {i}", f"2025-{i:02d}-15" if i <= 12 else f"2026-{i-12:02d}-15", "Rs. 1,250", "Success")
        for i in range(1, 15)
    ]
    c.executemany("INSERT OR IGNORE INTO payment_history VALUES (?, ?, ?, ?, ?, ?)", months_data)
    
    c.execute("PRAGMA table_info(claims)")
    clm_columns = [row[1] for row in c.fetchall()]
    if "claim_type" not in clm_columns:
        c.execute("ALTER TABLE claims ADD COLUMN claim_type TEXT DEFAULT 'Health'")

    c.execute("INSERT OR IGNORE INTO claims (claim_id, policy_no, claim_type, incident_type, claim_amt, claim_date, status) VALUES ('CLM-1001', 'MAG-IND-2024-88', 'Health', 'Hospitalization ICU', 'Rs. 45,000', '2026-02-10', 'Approved')")
    
    conn.commit()
    conn.close()

init_db()

def main(page: ft.Page):
    page.title = "Magadha Life & Health Insurance"
    page.window_width = 440
    page.window_height = 870
    page.padding = 0
    page.bgcolor = "#F1F5F9"

    current_mobile = [""]
    user_salutation = ["Mr."]
    user_name = [""]
    current_policy = ["MAG-IND-2024-88"]
    current_aadhaar = ["XXXX-XXXX-7892"]
    nominee_info = ["Family Nominee"]
    eye_open = [False]
    card_side = ["life"]

    def toast(msg, color="#312E81"):
        snack = ft.SnackBar(ft.Text(msg, color="white", weight="bold"), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    user_greeting_txt = ft.Text("Hi User", size=16, weight="bold", color="#1E1B4B")

    # Front Side: Life Insurance Card
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
        ft.Text("5412  8801  9924  7710", size=15, weight="bold", color="white", font_family="monospace"),
        ft.Row([
            ft.Column([
                ft.Text("INSURED MEMBER", size=8, color="#CBD5E1", weight="bold"),
                ft.Text(f"{user_name[0].upper() or 'VALUED CUSTOMER'}", size=11, weight="bold", color="white")
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

    # Back Side: Health Insurance Card
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
        ft.Text("4532  6612  3341  8821", size=15, weight="bold", color="white", font_family="monospace"),
        ft.Row([
            ft.Column([
                ft.Text("PRIMARY HOLDER", size=8, color="#E2E8F0", weight="bold"),
                ft.Text(f"{user_name[0].upper() or 'VALUED CUSTOMER'}", size=11, weight="bold", color="white")
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
        width=360,
        height=165,
        padding=14,
        border_radius=16,
        bgcolor="#0F172A",
        shadow=ft.BoxShadow(blur_radius=14, color="#02061730"),
        animate_rotation=ft.Animation(450, "easeInOut"),
        rotate=0
    )

    def trigger_card_flip(e):
        virtual_card_container.rotate = math.pi * 0.5
        page.update()
        time.sleep(0.2)

        if card_side[0] == "life":
            card_side[0] = "health"
            virtual_card_container.content = health_card_content
            virtual_card_container.bgcolor = "#064E3B"
        else:
            card_side[0] = "life"
            virtual_card_container.content = life_card_content
            virtual_card_container.bgcolor = "#0F172A"

        virtual_card_container.rotate = math.pi
        page.update()
        time.sleep(0.2)
        virtual_card_container.rotate = 0
        page.update()

    virtual_card_container.on_click = trigger_card_flip

    amt_label = ft.Text("••••••••", size=17, weight="bold", color="#020617")
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
                ft.Container(
                    content=ft.Text("ACTIVE", size=9, weight="bold", color="#047857"),
                    bgcolor="#D1FAE5",
                    padding=4,
                    border_radius=4
                )
            ], alignment="spaceBetween"),
            ft.Text(f"user policy no : {current_policy[0]}", size=12, color="#0F172A", weight="bold"),
            ft.Row([
                ft.Row([ft.Text("claim amount :", size=12, color="#1E293B", weight="bold"), amt_label]),
                eye_btn
            ], alignment="spaceBetween"),
            ft.Divider(height=4, color="#CBD5E1"),
            ft.Text("Death Reason Payout Breakdown:", size=11, weight="bold", color="#0F172A"),
            ft.Row([
                ft.Text("• Natural Death: Rs. 15,00,000", size=10, color="#1E293B", weight="bold"),
                ft.Text("• Accident: Rs. 30,00,000", size=10, color="#047857", weight="bold")
            ], alignment="spaceBetween"),
            ft.Text("• Critical Illness (Heart Attack): Rs. 20,00,000", size=10, color="#B91C1C", weight="bold"),
            ft.Container(
                content=ft.Row([
                    ft.Icon("assignment_ind", size=13, color="#1E1B4B"),
                    ft.Text(f"Nominee Guaranteed: {nominee_info[0]} ki matrame settlement cheyabadunu.", size=9, weight="bold", color="#1E1B4B")
                ], spacing=4),
                bgcolor="#E0E7FF",
                padding=4,
                border_radius=4
            )
        ], spacing=4),
        padding=12,
        border_radius=14,
        bgcolor="#FFFFFF",
        border=ft.border.all(1.5, "#94A3B8"),
        shadow=ft.BoxShadow(blur_radius=10, color="#0F172A15")
    )

    claim_type_field = ft.Dropdown(
        label="Claim Type",
        options=[ft.dropdown.Option("Life Insurance"), ft.dropdown.Option("Health Insurance")],
        bgcolor="white",
        color="#0F172A"
    )
    claim_reason = ft.TextField(label="Incident Description", hint_text="e.g. Heart Attack, Hospital Bill", bgcolor="white", color="#0F172A")
    claim_amount = ft.TextField(label="Claim Amount (Rs)", keyboard_type=ft.KeyboardType.NUMBER, bgcolor="white", color="#0F172A")

    def on_submit_claim(e):
        if not claim_reason.value or not claim_amount.value:
            toast("Please fill all details", "#B91C1C")
            return
        new_id = f"CLM-{datetime.datetime.now().strftime('%M%S')}"
        conn3 = sqlite3.connect(DB_FILE)
        c3 = conn3.cursor()
        c3.execute("INSERT INTO claims (claim_id, policy_no, claim_type, incident_type, claim_amt, claim_date, status) VALUES (?, ?, ?, ?, ?, ?, 'Under Review')",
                   (new_id, current_policy[0], claim_type_field.value or "Health", claim_reason.value, f"Rs. {claim_amount.value}", datetime.date.today().strftime('%Y-%m-%d')))
        conn3.commit()
        conn3.close()
        claim_sheet.open = False
        reload_claims()
        toast(f"Claim {new_id} Submitted!", "#047857")
        page.update()

    claim_sheet = ft.BottomSheet(
        ft.Container(
            content=ft.Column([
                ft.Text("Submit Insurance Claim Ticket", size=15, weight="bold", color="#0F172A"),
                claim_type_field,
                claim_reason,
                claim_amount,
                ft.ElevatedButton("Submit Claim Ticket", bgcolor="#312E81", color="white", width=340, height=45, on_click=on_submit_claim)
            ], spacing=10),
            padding=20,
            bgcolor="white"
        )
    )
    page.overlay.append(claim_sheet)

    def trigger_life_claim(e):
        claim_type_field.value = "Life Insurance"
        claim_sheet.open = True
        page.update()

    def trigger_health_claim(e):
        claim_type_field.value = "Health Insurance"
        claim_sheet.open = True
        page.update()

    action_buttons = ft.Row([
        ft.ElevatedButton(
            "Life Claim",
            icon="family_restroom",
            bgcolor="#312E81",
            color="white",
            height=42,
            expand=True,
            on_click=trigger_life_claim
        ),
        ft.ElevatedButton(
            "Health Claim",
            icon="local_hospital",
            bgcolor="#047857",
            color="white",
            height=42,
            expand=True,
            on_click=trigger_health_claim
        )
    ], spacing=8)

    home_content_view = ft.Column([
        user_greeting_txt,
        virtual_card_container,
        coverage_detail_box,
        action_buttons,
        ft.Text("Live fulfilled", size=16, weight="bold", color="#0F172A", italic=True, text_align="center"),
        ft.Text("Instant cashless access & Nominee security", size=11, color="#334155", weight="bold", text_align="center")
    ], horizontal_alignment="center", spacing=10, scroll=ft.ScrollMode.AUTO)

    profile_name_txt = ft.Text("Name: User", size=13, weight="bold", color="#0F172A")
    profile_mobile_txt = ft.Text("Mobile: +91 ", size=12, color="#0F172A", weight="bold")

    customer_info_view = ft.Column([
        ft.Text("Customer Policy Schedule", size=15, weight="bold", color="#0F172A"),
        ft.Container(
            content=ft.Column([
                profile_name_txt,
                ft.Text(f"Policy No: {current_policy[0]}", size=12, color="#312E81", weight="bold"),
                ft.Text(f"Aadhaar: {current_aadhaar[0]}", size=12, color="#0F172A", weight="bold"),
                profile_mobile_txt,
                ft.Text(f"Nominee: {nominee_info[0]}", size=12, color="#047857", weight="bold"),
                ft.Divider(height=1),
                ft.Text("Plan: Magadha Life & Health Twin Shield", size=12, weight="bold", color="#0F172A"),
                ft.Text("Reg Date: 2025-01-15", size=11, color="#334155", weight="bold"),
                ft.Text("Valid Upto: 2027-01-14", size=11, color="#334155", weight="bold"),
                ft.Text("Monthly Premium: Rs. 1,250", size=12, color="#047857", weight="bold")
            ], spacing=4),
            padding=12,
            bgcolor="#FFFFFF",
            border_radius=10,
            border=ft.border.all(1, "#CBD5E1")
        )
    ], spacing=6)

    history_items = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=450)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT txn_id, month_paid, payment_date, amount_paid, status FROM payment_history ORDER BY rowid DESC")
    pay_history = c.fetchall()
    conn.close()

    for p in pay_history:
        history_items.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(f"{p[1]} ({p[0]})", size=11, weight="bold", color="#0F172A"),
                        ft.Text(f"Date: {p[2]}", size=10, color="#334155", weight="bold")
                    ], spacing=1),
                    ft.Column([
                        ft.Text(p[3], size=11, weight="bold", color="#047857"),
                        ft.Text(p[4], size=10, color="#312E81", weight="bold")
                    ], alignment="spaceBetween", spacing=1)
                ], alignment="spaceBetween"),
                padding=8,
                bgcolor="#FFFFFF",
                border_radius=8,
                border=ft.border.all(1, "#CBD5E1")
            )
        )

    history_view = ft.Column([
        ft.Text(f"Payment History ({len(pay_history)} Months Paid)", size=14, weight="bold", color="#0F172A"),
        history_items
    ], spacing=6)

    claims_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)

    def reload_claims():
        claims_col.controls.clear()
        conn2 = sqlite3.connect(DB_FILE)
        c2 = conn2.cursor()
        c2.execute("SELECT claim_id, policy_no, claim_type, incident_type, claim_amt, status FROM claims ORDER BY claim_id DESC")
        for clm in c2.fetchall():
            claims_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"{clm[0]} ({clm[2]})", weight="bold", color="#1E1B4B", size=12),
                            ft.Text(clm[5], weight="bold", color="#047857" if clm[5] == "Approved" else "#D97706", size=11)
                        ], alignment="spaceBetween"),
                        ft.Text(clm[3], size=11, color="#0F172A", weight="bold"),
                        ft.Row([
                            ft.Text(f"Policy: {clm[1]}", size=10, color="#334155", weight="bold"),
                            ft.Text(clm[4], weight="bold", color="#0F172A", size=11)
                        ], alignment="spaceBetween")
                    ], spacing=2),
                    bgcolor="#FFFFFF",
                    padding=8,
                    border_radius=8,
                    border=ft.border.all(1, "#CBD5E1")
                )
            )
        conn2.close()

    reload_claims()

    claims_view = ft.Column([
        ft.Text("Track Claims", weight="bold", size=14, color="#0F172A"),
        claims_col
    ], spacing=8, scroll=ft.ScrollMode.AUTO)

    explore_view = ft.Column([
        ft.Text("Available Plans", size=14, weight="bold", color="#0F172A"),
        ft.Container(
            content=ft.Column([
                ft.Text("Magadha Critical Heart & Stroke Shield", weight="bold", size=12, color="#0F172A"),
                ft.Text("Rs. 25 Lakhs • Rs. 1,850/mo", color="#1E1B4B", size=11, weight="bold"),
                ft.ElevatedButton("Enroll Plan", bgcolor="#312E81", color="white", width=180, height=35, on_click=lambda _: toast("Policy Enrolled!"))
            ], spacing=4),
            padding=10,
            bgcolor="#FFFFFF",
            border_radius=8,
            border=ft.border.all(1, "#CBD5E1")
        )
    ], spacing=8)

    profile_card_name = ft.Text("Name: User", size=13, weight="bold", color="#0F172A")
    profile_card_mobile = ft.Text("Mobile: +91 ", size=12, color="#0F172A", weight="bold")

    profile_view = ft.Column([
        ft.Text("Customer Profile", size=14, weight="bold", color="#0F172A"),
        profile_card_name,
        profile_card_mobile,
        ft.Text(f"Aadhaar: {current_aadhaar[0]}", size=12, color="#0F172A", weight="bold"),
        ft.Text(f"Nominee: {nominee_info[0]}", size=12, color="#047857", weight="bold"),
        ft.Divider(),
        ft.ElevatedButton("Logout", bgcolor="#FEE2E2", color="#B91C1C", width=180, height=38, on_click=lambda _: switch_screen("login"))
    ], spacing=8)

    right_display = ft.Container(content=home_content_view, expand=True, padding=10)

    def switch_nav_tab(target):
        if target == "home":
            right_display.content = home_content_view
        elif target == "policy":
            right_display.content = customer_info_view
        elif target == "history":
            right_display.content = history_view
        elif target == "claims":
            right_display.content = claims_view
        elif target == "explore":
            right_display.content = explore_view
        elif target == "profile":
            right_display.content = profile_view
        page.update()

    left_vertical_sidebar = ft.Container(
        content=ft.Column([
            ft.TextButton("Home", icon="home", on_click=lambda _: switch_nav_tab("home")),
            ft.TextButton("Details", icon="badge", on_click=lambda _: switch_nav_tab("policy")),
            ft.TextButton("History", icon="history", on_click=lambda _: switch_nav_tab("history")),
            ft.TextButton("Claims", icon="receipt_long", on_click=lambda _: switch_nav_tab("claims")),
            ft.TextButton("Explore", icon="storefront", on_click=lambda _: switch_nav_tab("explore")),
            ft.TextButton("Profile", icon="person", on_click=lambda _: switch_nav_tab("profile")),
        ], spacing=10, alignment="start"),
        width=115,
        padding=10,
        bgcolor="#F8FAFC",
        border=ft.border.only(right=ft.BorderSide(1, "#CBD5E1"))
    )

    top_bar = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Container(content=ft.Text("M", size=16, weight="bold", color="white"), width=32, height=32, bgcolor="#1E1B4B", border_radius=6, alignment=ft.Alignment(0, 0)),
                ft.Text("MAGADHA", size=15, weight="bold", color="#0F172A")
            ], spacing=6),
            ft.TextButton(
                content=ft.Row([ft.Icon("support_agent", color="#1E1B4B", size=16), ft.Text("Help", color="#1E1B4B", size=12, weight="bold")], spacing=2),
                on_click=lambda _: toast("Helpline: 1800-MAGADHA")
            )
        ], alignment="spaceBetween"),
        padding=10,
        bgcolor="white",
        border=ft.border.only(bottom=ft.BorderSide(1, "#CBD5E1"))
    )

    home_screen = ft.Container(
        content=ft.Column([
            top_bar,
            ft.Row([left_vertical_sidebar, right_display], expand=True, spacing=0)
        ], expand=True, spacing=0),
        expand=True,
        visible=False
    )

    # ----------------------------------------------------
    # SCREEN 3: VERIFY DETAILS FORM (Post-OTP)
    # ----------------------------------------------------
    v_name = ft.TextField(label="Customer Full Name", label_style=ft.TextStyle(color="#0F172A", weight="bold"), bgcolor="#F8FAFC", border_color="#475569", color="#0F172A", text_size=14, width=310)
    v_policy = ft.TextField(label="Policy Number", label_style=ft.TextStyle(color="#0F172A", weight="bold"), value="MAG-IND-2024-88", bgcolor="#F8FAFC", border_color="#475569", color="#0F172A", text_size=14, width=310)
    
    # Linked Mobile Box with super clear dark prefix & dark text
    v_mobile = ft.TextField(
        label="Linked Mobile Number",
        label_style=ft.TextStyle(color="#0F172A", weight="bold"),
        prefix=ft.Text("+91 ", size=14, weight="bold", color="#0F172A"),
        keyboard_type=ft.KeyboardType.PHONE,
        bgcolor="#F8FAFC",
        border_color="#475569",
        color="#0F172A",
        text_size=14,
        width=310
    )
    v_aadhaar = ft.TextField(label="Aadhaar Number", label_style=ft.TextStyle(color="#0F172A", weight="bold"), value="XXXX-XXXX-7892", bgcolor="#F8FAFC", border_color="#475569", color="#0F172A", text_size=14, width=310)

    def on_confirm_verify_details(e):
        if not v_name.value or not v_mobile.value:
            toast("Please enter all details!", "#B91C1C")
            return
        user_name[0] = v_name.value.strip()
        current_mobile[0] = v_mobile.value.strip()
        current_policy[0] = v_policy.value.strip()
        current_aadhaar[0] = v_aadhaar.value.strip()

        user_greeting_txt.value = f"Hi {user_salutation[0]} {user_name[0]}"
        profile_name_txt.value = f"Name: {user_salutation[0]} {user_name[0]}"
        profile_card_name.value = f"Name: {user_salutation[0]} {user_name[0]}"
        profile_mobile_txt.value = f"Mobile: +91 {current_mobile[0]}"
        profile_card_mobile.value = f"Mobile: +91 {current_mobile[0]}"

        toast("Policy & Identity Verified!", "#047857")
        switch_screen("home")

    verify_details_card = ft.Container(
        content=ft.Column([
            ft.Icon("verified_user", size=40, color="#1E1B4B"),
            ft.Text("Verify Customer Identity", size=18, weight="bold", color="#0F172A"),
            ft.Text("Confirm your policy & linked Aadhaar details", size=12, color="#0F172A", weight="bold"),
            v_name,
            v_policy,
            v_mobile,
            v_aadhaar,
            ft.Container(height=5),
            ft.ElevatedButton("Verify & Unlock Portal", width=310, height=45, bgcolor="#1E1B4B", color="white", on_click=on_confirm_verify_details)
        ], alignment="center", horizontal_alignment="center", spacing=10),
        padding=25,
        border_radius=20,
        border=ft.border.all(1.5, "#CBD5E1"),
        shadow=ft.BoxShadow(blur_radius=15, color="#0F172A15"),
        bgcolor="white",
        width=360
    )

    verify_details_screen = ft.Container(
        content=verify_details_card,
        alignment=ft.Alignment(0, 0),
        expand=True,
        visible=False
    )

    # ----------------------------------------------------
    # SCREEN 2: OTP SCREEN (0/1 counter completely gone)
    # ----------------------------------------------------
    def create_otp_box():
        tf = ft.TextField(
            width=52,
            height=54,
            text_align="center",
            text_size=22,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            bgcolor="#F8FAFC",
            border_color="#475569",
            color="#0F172A",
            content_padding=0
        )
        return ft.Container(content=tf, width=52, height=54, clip_behavior=ft.ClipBehavior.HARD_EDGE), tf

    box1, t1 = create_otp_box()
    box2, t2 = create_otp_box()
    box3, t3 = create_otp_box()
    box4, t4 = create_otp_box()
    t1.autofocus = True

    boxes_row = ft.Container(
        content=ft.Row([box1, box2, box3, box4], alignment="center", spacing=10),
        alignment=ft.Alignment(0, 0)
    )

    verified_ring = ft.Container(
        content=ft.Icon("check", color="white", size=40),
        width=70,
        height=70,
        border_radius=35,
        bgcolor="#047857",
        alignment=ft.Alignment(0, 0),
        scale=0.1,
        opacity=0.0,
        shadow=ft.BoxShadow(blur_radius=20, color="#04785780"),
        animate_scale=ft.Animation(600, "elasticOut"),
        animate_opacity=ft.Animation(300, "easeIn")
    )

    otp_status_lbl = ft.Text("Enter 4-digit code sent to mobile\n(Demo OTP: 1234)", size=13, color="#0F172A", weight="bold", text_align="center")

    def run_tick_animation_and_enter():
        boxes_row.visible = False
        verified_ring.opacity = 1.0
        verified_ring.scale = 1.2
        otp_status_lbl.value = "Verified! Confirm Identity."
        otp_status_lbl.color = "#047857"
        otp_status_lbl.weight = "bold"
        page.update()

        def proceed_after_delay():
            time.sleep(1.0)
            switch_screen("verify_details")

        threading.Thread(target=proceed_after_delay, daemon=True).start()

    def on_t1(e):
        val = t1.value or ""
        if len(val) > 1:
            t1.value = val[-1]
        if t1.value:
            t2.focus()
        page.update()

    def on_t2(e):
        val = t2.value or ""
        if len(val) > 1:
            t2.value = val[-1]
        if t2.value:
            t3.focus()
        page.update()

    def on_t3(e):
        val = t3.value or ""
        if len(val) > 1:
            t3.value = val[-1]
        if t3.value:
            t4.focus()
        page.update()

    def on_t4(e):
        val = t4.value or ""
        if len(val) > 1:
            t4.value = val[-1]
        page.update()
        otp = f"{t1.value or ''}{t2.value or ''}{t3.value or ''}{t4.value or ''}".strip()
        if otp == "1234":
            run_tick_animation_and_enter()

    t1.on_change = on_t1
    t2.on_change = on_t2
    t3.on_change = on_t3
    t4.on_change = on_t4

    def on_verify_btn(e):
        otp = f"{t1.value or ''}{t2.value or ''}{t3.value or ''}{t4.value or ''}".strip()
        if otp == "1234":
            run_tick_animation_and_enter()
        else:
            toast("Invalid OTP! Enter 1234", "#B91C1C")

    otp_card = ft.Container(
        content=ft.Column([
            ft.Text("OTP Verification", size=22, weight="bold", color="#0F172A"),
            otp_status_lbl,
            ft.Container(height=18),
            ft.Stack([
                boxes_row,
                ft.Container(content=verified_ring, alignment=ft.Alignment(0, 0), height=70)
            ], alignment=ft.Alignment(0, 0)),
            ft.Container(height=25),
            ft.ElevatedButton("Verify & Proceed", width=280, height=48, bgcolor="#1E1B4B", color="white", on_click=on_verify_btn),
            ft.TextButton("Change Details", on_click=lambda _: switch_screen("login"))
        ], alignment="center", horizontal_alignment="center", spacing=14),
        bgcolor="white",
        padding=30,
        border_radius=20,
        border=ft.border.all(1.5, "#CBD5E1"),
        shadow=ft.BoxShadow(blur_radius=18, color="#0F172A15"),
        width=360
    )

    otp_screen = ft.Container(
        content=otp_card,
        alignment=ft.Alignment(0, 0),
        expand=True,
        visible=False
    )

    # ----------------------------------------------------
    # SCREEN 1: LOGIN (Clear dark "+91" prefix & dark text)
    # ----------------------------------------------------
    title_dropdown = ft.Dropdown(
        label="Title",
        label_style=ft.TextStyle(color="#0F172A", weight="bold"),
        width=95,
        options=[
            ft.dropdown.Option("Mr."),
            ft.dropdown.Option("Mrs."),
            ft.dropdown.Option("Ms.")
        ],
        value="Mr.",
        bgcolor="#F8FAFC",
        border_color="#475569",
        color="#0F172A",
        border_radius=12
    )

    name_field = ft.TextField(
        label="Full Name",
        label_style=ft.TextStyle(color="#0F172A", weight="bold"),
        hint_text="e.g. Kiran Kumar",
        hint_style=ft.TextStyle(color="#64748B"),
        width=205,
        bgcolor="#F8FAFC",
        border_color="#475569",
        color="#0F172A",
        border_radius=12
    )

    # Clean Dark Prefix (+91)
    phone_box = ft.TextField(
        label="Mobile Number",
        label_style=ft.TextStyle(color="#0F172A", weight="bold"),
        prefix=ft.Text("+91 ", size=14, weight="bold", color="#0F172A"),
        hint_text="10-digit number",
        hint_style=ft.TextStyle(color="#64748B"),
        keyboard_type=ft.KeyboardType.PHONE,
        width=310,
        bgcolor="#F8FAFC",
        border_color="#475569",
        color="#0F172A",
        border_radius=12
    )

    def show_permissions_and_proceed(m_val, n_val, s_val):
        def on_grant_permissions(e):
            page.dialog.open = False
            current_mobile[0] = m_val
            user_name[0] = n_val
            user_salutation[0] = s_val
            v_name.value = n_val
            v_mobile.value = m_val

            otp_status_lbl.value = f"Enter 4-digit code sent to +91 {m_val}\n(Demo OTP: 1234)"
            switch_screen("otp")
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text("App Permissions Required", size=16, weight="bold", color="#0F172A"),
            content=ft.Column([
                ft.ListTile(leading=ft.Icon("camera_alt", color="#1E1B4B"), title=ft.Text("Camera Permission", size=12, weight="bold", color="#0F172A"), subtitle=ft.Text("For instant document & bill scans", size=11, color="#334155")),
                ft.ListTile(leading=ft.Icon("folder", color="#1E1B4B"), title=ft.Text("Storage Permission", size=12, weight="bold", color="#0F172A"), subtitle=ft.Text("For claim invoices & policy docs", size=11, color="#334155")),
                ft.ListTile(leading=ft.Icon("sms", color="#1E1B4B"), title=ft.Text("SMS Access", size=12, weight="bold", color="#0F172A"), subtitle=ft.Text("For secure instant OTP login", size=11, color="#334155")),
            ], tight=True),
            actions=[
                ft.TextButton("Deny", on_click=lambda _: setattr(page.dialog, "open", False) or page.update()),
                ft.ElevatedButton("Allow & Continue", bgcolor="#1E1B4B", color="white", on_click=on_grant_permissions)
            ]
        )
        page.dialog.open = True
        page.update()

    def on_get_otp_click(e):
        m_val = (phone_box.value or "").strip()
        n_val = (name_field.value or "").strip()
        s_val = title_dropdown.value or "Mr."

        if not n_val:
            toast("Please enter your Full Name", "#B91C1C")
            return
        if len(m_val) == 10 and m_val.isdigit():
            show_permissions_and_proceed(m_val, n_val, s_val)
        else:
            toast("Enter a valid 10-digit mobile number", "#B91C1C")

    login_card = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("M", size=36, weight="bold", color="white"),
                width=75,
                height=75,
                bgcolor="#1E1B4B",
                border_radius=18,
                alignment=ft.Alignment(0, 0)
            ),
            ft.Text("MAGADHA", size=24, weight="bold", color="#0F172A"),
            ft.Text("Life & Health Insurance Portal", size=13, color="#334155", weight="bold"),
            ft.Container(height=5),
            ft.Row([title_dropdown, name_field], width=310, spacing=10),
            phone_box,
            ft.ElevatedButton(
                "Get OTP",
                width=310,
                height=48,
                bgcolor="#1E1B4B",
                color="white",
                on_click=on_get_otp_click
            )
        ], alignment="center", horizontal_alignment="center", spacing=14),
        padding=30,
        border_radius=20,
        border=ft.border.all(1.5, "#CBD5E1"),
        shadow=ft.BoxShadow(blur_radius=15, color="#0F172A15"),
        bgcolor="white",
        width=360
    )

    login_screen = ft.Container(
        content=login_card,
        alignment=ft.Alignment(0, 0),
        expand=True,
        visible=False
    )

    # ----------------------------------------------------
    # SCREEN 0: "M" LOGO ZOOM ANIMATION
    # ----------------------------------------------------
    m_char = ft.Text("M", size=60, weight="bold", color="white")
    m_zoom_box = ft.Container(
        content=m_char,
        width=100,
        height=100,
        bgcolor="#1E1B4B",
        border_radius=25,
        alignment=ft.Alignment(0, 0),
        animate=ft.Animation(800, "easeInCubic"),
        animate_opacity=ft.Animation(600, "easeIn")
    )

    splash_screen = ft.Container(
        content=ft.Column([
            m_zoom_box,
            ft.Text("MAGADHA INSURANCE", size=20, weight="bold", color="#0F172A")
        ], alignment="center", horizontal_alignment="center", spacing=15),
        alignment=ft.Alignment(0, 0),
        expand=True,
        visible=True
    )

    def run_splash_zoom():
        time.sleep(0.5)
        m_zoom_box.width = 950
        m_zoom_box.height = 950
        m_zoom_box.border_radius = 450
        m_char.size = 350
        m_zoom_box.opacity = 0.0
        page.update()
        time.sleep(0.7)
        switch_screen("login")

    def switch_screen(name):
        splash_screen.visible = (name == "splash")
        login_screen.visible = (name == "login")
        otp_screen.visible = (name == "otp")
        verify_details_screen.visible = (name == "verify_details")
        home_screen.visible = (name == "home")
        
        if name == "otp":
            t1.value = ""
            t2.value = ""
            t3.value = ""
            t4.value = ""
            boxes_row.visible = True
            verified_ring.opacity = 0.0
            verified_ring.scale = 0.1
            t1.focus()
            
        page.update()

    page.add(
        ft.Stack([
            splash_screen,
            login_screen,
            otp_screen,
            verify_details_screen,
            home_screen
        ], expand=True)
    )

    threading.Thread(target=run_splash_zoom, daemon=True).start()

# Render ASGI Mount
app = flet_fastapi.app(main)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
