"""One-click installer for Travellers Rest Planner.

Run this and it does everything:
  1. Installs Python dependencies
  2. Finds your game install
  3. Extracts all game data (items, recipes, icons, maps, etc.)
  4. Launches the planner

Usage:
  python install.py
"""
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def run(cmd, desc, check=True):
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"{'='*60}\n")
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        print(f"\n[!] failed: {desc}")
        print(f"    command: {cmd}")
        print(f"    try running it manually and see what the error says")
        input("\npress enter to continue anyway, or ctrl+c to quit...")

def main():
    print("""
    ========================================
      Travellers Rest Planner — Installer
    ========================================

    this will:
      1. install python packages
      2. find your game
      3. extract game data (~2 min)
      4. launch the planner

    make sure travellers rest is installed on this PC.
    """)

    input("press enter to start...")

    # Step 1: Install deps
    run(
        f'"{sys.executable}" -m pip install -r requirements.txt',
        "installing python dependencies"
    )

    # Step 2: Check game is findable
    print(f"\n{'='*60}")
    print(f"  finding your game install")
    print(f"{'='*60}\n")
    try:
        sys.path.insert(0, ROOT)
        from planner.gamepath import find_game_data_dir
        game_dir = find_game_data_dir()
        print(f"  found: {game_dir}")
    except FileNotFoundError as e:
        print(f"\n[!] couldn't find travellers rest automatically.\n")
        print(str(e))
        print()
        game_dir = input("paste the path to your TravellersRest_Data folder: ").strip().strip('"')
        if game_dir:
            os.environ["TR_GAME_DIR"] = game_dir
            print(f"  using: {game_dir}")
        else:
            print("no path given, quitting")
            sys.exit(1)

    # Step 3: Extract game data
    scripts = [
        ("scripts/dump_mono.py",     "extracting items, recipes, crops, shops, quests..."),
        ("scripts/dump_i2l.py",      "extracting localization (30 languages)..."),
        ("scripts/dump_icons.py",    "extracting item icons..."),
        ("scripts/dump_coins.py",    "extracting coin sprites..."),
        ("scripts/dump_hotspots.py", "extracting map hotspots..."),
        ("scripts/synthesize.py",    "building summary tables..."),
    ]

    for script, desc in scripts:
        run(f'"{sys.executable}" {script}', desc, check=False)

    # Optional: render maps (slow, skip if they want)
    print(f"\n{'='*60}")
    print(f"  render tilemap backgrounds? (takes ~3 min, uses ~500mb ram)")
    print(f"{'='*60}\n")
    choice = input("render maps? [y/N] ").strip().lower()
    if choice in ("y", "yes"):
        run(f'"{sys.executable}" scripts/dump_maps.py', "rendering scene maps...")

    # Step 4: Verify
    print(f"\n{'='*60}")
    print(f"  verifying installation")
    print(f"{'='*60}\n")

    checks = {
        "data/i18n.json": "localization",
        "data/items.json": "items database",
        "data/recipes.csv": "recipes",
        "data/crops.csv": "crops",
    }
    icons = len([f for f in os.listdir("data/icons") if f.endswith(".png")]) if os.path.isdir("data/icons") else 0

    all_good = True
    for path, name in checks.items():
        exists = os.path.exists(path)
        status = "ok" if exists else "MISSING"
        if not exists:
            all_good = False
        print(f"  [{status}] {name}: {path}")
    print(f"  [{'ok' if icons > 100 else 'low'}] icons: {icons} extracted")

    if not all_good:
        print("\n[!] some files are missing. the planner might not work fully.")
        print("    try re-running the failed extraction script manually.\n")

    # Step 5: Launch
    print(f"\n{'='*60}")
    print(f"  done! launching planner...")
    print(f"{'='*60}\n")
    print(f"  open http://127.0.0.1:8765/ in your browser\n")
    print(f"  press ctrl+c to stop the server\n")

    subprocess.run([sys.executable, "-m", "planner"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\ncancelled")
    except Exception as e:
        print(f"\n\nerror: {e}")
        input("\npress enter to exit...")
