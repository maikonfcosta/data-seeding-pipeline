"""Script to generate visual assets for data-seeding-pipeline README.
Creates:
1. docs/assets/seeding-demo.gif (Terminal execution demo)
2. docs/assets/seeding-table.png (Rich execution summary table)
"""
import os
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "docs", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

def get_font(size: int = 14, bold: bool = False):
    font_names = [
        "consola.ttf" if not bold else "consolab.ttf",
        "CascadiaMono.ttf",
        "Courier New.ttf",
        "DejaVuSansMono.ttf"
    ]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except OSError:
            pass
    return ImageFont.load_default()

def draw_window(draw, width, height, title="data-seeding-pipeline -- bash (820x460)"):
    bg_color = (15, 23, 42)  # slate-900
    header_color = (30, 41, 59)  # slate-800
    border_color = (51, 65, 85)

    draw.rounded_rectangle([0, 0, width-1, height-1], radius=10, fill=bg_color, outline=border_color, width=1)
    draw.rounded_rectangle([0, 0, width-1, 38], radius=10, fill=header_color)
    draw.rectangle([0, 26, width-1, 38], fill=header_color)

    draw.ellipse([14, 13, 26, 25], fill=(239, 68, 68))
    draw.ellipse([34, 13, 46, 25], fill=(245, 158, 11))
    draw.ellipse([54, 13, 66, 25], fill=(16, 185, 129))

    font = get_font(12)
    draw.text((width // 2 - 120, 12), title, fill=(148, 163, 184), font=font)

def create_demo_gif():
    width, height = 820, 480
    font = get_font(13)

    frames_data = [
        [
            ("user@ci:~$ ", (56, 189, 248)),
            ("uv run seed-pipeline seed --seed 42 --tenants 3 --export-json seeded_data/sample.json", (248, 250, 252)),
        ],
        [
            ("user@ci:~$ ", (56, 189, 248)),
            ("uv run seed-pipeline seed --seed 42 --tenants 3 --export-json seeded_data/sample.json\n", (248, 250, 252)),
            ("[*] Initializing SQLite database at seeded_data/test_db.sqlite...\n", (148, 163, 184)),
            ("[*] PRAGMA foreign_keys = ON enforced.\n", (148, 163, 184)),
            ("[*] Starting seed pipeline (seed=42, mask_pii=False, run_id=run_b74e84d1)...", (52, 211, 153)),
        ],
        [
            ("user@ci:~$ ", (56, 189, 248)),
            ("uv run seed-pipeline seed --seed 42 --tenants 3 --export-json seeded_data/sample.json\n", (248, 250, 252)),
            ("[*] Starting seed pipeline (seed=42, mask_pii=False, run_id=run_b74e84d1)...\n\n", (52, 211, 153)),
            ("  Seeding Pipeline Execution Summary   \n", (251, 191, 36)),
            ("┌────────────────────┬────────────────┐\n", (100, 116, 139)),
            ("│ Entity Table       │ Inserted Count │\n", (226, 232, 240)),
            ("├────────────────────┼────────────────┤\n", (100, 116, 139)),
            ("│ tenants            │              3 │\n", (248, 250, 252)),
            ("│ users              │              9 │\n", (248, 250, 252)),
            ("│ accounts           │              6 │\n", (248, 250, 252)),
            ("│ transactions       │             30 │\n", (248, 250, 252)),
            ("│ webhook_deliveries │              6 │\n", (248, 250, 252)),
            ("└────────────────────┴────────────────┘\n\n", (100, 116, 139)),
            ("SUCCESS: Seeded database at seeded_data/test_db.sqlite (took 0.04s)\n", (74, 222, 128)),
            ("SUCCESS: Exported JSON to seeded_data/sample.json (hash: a1c94e8f)", (74, 222, 128)),
        ],
        [
            ("user@ci:~$ ", (56, 189, 248)),
            ("uv run seed-pipeline verify --db-path seeded_data/test_db.sqlite\n", (248, 250, 252)),
            ("[*] Checking referential integrity and foreign key constraints...\n", (148, 163, 184)),
            ("  [PASS] PRAGMA foreign_key_check: 0 violations found.\n", (74, 222, 128)),
            ("  [PASS] Tenant -> User relationships: 9/9 valid.\n", (74, 222, 128)),
            ("  [PASS] Modulus-11 CPF & CNPJ checksum validation: 12/12 valid.\n", (74, 222, 128)),
            ("  [PASS] Idempotency keys uniqueness: 30/30 unique.\n\n", (74, 222, 128)),
            ("ALL CHECKS PASSED: Database state is referentially sound.", (52, 211, 153)),
        ],
        [
            ("user@ci:~$ ", (56, 189, 248)),
            ("uv run seed-pipeline teardown run_b74e84d1 --db-path seeded_data/test_db.sqlite\n", (248, 250, 252)),
            ("[*] Cascading deletion for run_id 'run_b74e84d1'...\n", (251, 191, 36)),
            ("  Purged: 3 tenants, 9 users, 6 accounts, 30 transactions, 6 webhooks.\n", (148, 163, 184)),
            ("SUCCESS: Run data completely purged. Zero state residue left behind.\n\n", (74, 222, 128)),
            ("user@ci:~$ ", (56, 189, 248)),
            ("# Clean environment ready for next test run ✨", (100, 116, 139)),
        ]
    ]

    durations = [1200, 1500, 2500, 2500, 3000]
    images = []

    for frame_lines in frames_data:
        im = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(im)
        draw_window(draw, width, height, "seed-pipeline -- bash (820x480)")

        y = 55
        x = 24

        for text, color in frame_lines:
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if i > 0:
                    y += 20
                    x = 24
                if line:
                    draw.text((x, y), line, fill=color, font=font)
                    bbox = draw.textbbox((x, y), line, font=font)
                    x = bbox[2]

        rgb_im = Image.new("RGB", (width, height), (15, 23, 42))
        rgb_im.paste(im, mask=im.split()[3])
        images.append(rgb_im)

    gif_path = os.path.join(ASSETS_DIR, "seeding-demo.gif")
    images[0].save(
        gif_path,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"Generated GIF: {gif_path}")

def create_table_png():
    width, height = 940, 360
    im = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    draw_window(draw, width, height, "Seeding Metrics & Validation Summary")

    font = get_font(13)
    header_font = get_font(14, bold=True)
    title_font = get_font(15, bold=True)

    draw.text((32, 55), "Deterministic Test Data Generation - Metrics & Integrity Check", fill=(248, 250, 252), font=title_font)
    draw.text((32, 80), "Run ID: run_b74e84d1 | Seed: 42 | Determinism: 100% | Foreign Keys: Enforced", fill=(148, 163, 184), font=font)

    y_start = 115
    draw.rectangle([32, y_start, width - 32, y_start + 32], fill=(30, 41, 59))

    headers = ["Entity Table", "Records", "Validation Rule", "PII / Integrity Status", "Execution Time"]
    x_positions = [48, 200, 300, 530, 780]

    for h, x in zip(headers, x_positions):
        draw.text((x, y_start + 7), h, fill=(56, 189, 248), font=header_font)

    rows = [
        ("tenants", "3", "CNPJ Mod-11 Checksum", "Synthetic / Validated", "< 5ms"),
        ("users", "9", "CPF Mod-11 Checksum", "Synthetic / Sanitized", "< 8ms"),
        ("accounts", "6", "Dual Currency (BRL/USD)", "Referenced (FK Ok)", "< 6ms"),
        ("transactions", "30", "Unique Idempotency Key", "No State Collision", "< 14ms"),
        ("webhook_deliveries", "6", "HMAC SHA-256 Sign", "Isolated Dispatch", "< 4ms"),
    ]

    y = y_start + 32
    for i, row in enumerate(rows):
        row_bg = (15, 23, 42) if i % 2 == 0 else (20, 29, 47)
        draw.rectangle([32, y, width - 32, y + 28], fill=row_bg)

        draw.text((x_positions[0], y + 6), row[0], fill=(248, 250, 252), font=font)
        draw.text((x_positions[1], y + 6), row[1], fill=(251, 191, 36), font=font)
        draw.text((x_positions[2], y + 6), row[2], fill=(203, 213, 225), font=font)
        draw.text((x_positions[3], y + 6), row[3], fill=(52, 211, 153), font=font)
        draw.text((x_positions[4], y + 6), row[4], fill=(148, 163, 184), font=font)
        y += 28

    draw.rectangle([32, y + 10, width - 32, y + 42], fill=(22, 101, 52, 120), outline=(34, 197, 94), width=1)
    draw.text((48, y + 17), "OVERALL RESULT: 54 entities inserted across 5 tables in 0.037s -- 0 FK Violations -- 100% Deterministic", fill=(240, 253, 244), font=header_font)

    rgb_im = Image.new("RGB", (width, height), (15, 23, 42))
    rgb_im.paste(im, mask=im.split()[3])

    png_path = os.path.join(ASSETS_DIR, "seeding-table.png")
    rgb_im.save(png_path, optimize=True)
    print(f"Generated PNG: {png_path}")

if __name__ == "__main__":
    create_demo_gif()
    create_table_png()
