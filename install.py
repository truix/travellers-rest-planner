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
        print("tip: in Steam, right-click Travellers Rest -> Manage -> Browse local")
        print("     files. That opens the game's root. The path you want is that")
        print("     folder + \\Windows\\TravellersRest_Data")
        print()
        game_dir = input("paste the path to your TravellersRest_Data folder: ").strip().strip('"').strip("'")
        if not game_dir:
            print("no path given, quitting")
            sys.exit(1)
        # If they pasted the game root (no \Windows\TravellersRest_Data), fix it up
        if not os.path.exists(os.path.join(game_dir, "globalgamemanagers")):
            fixed = os.path.join(game_dir, "Windows", "TravellersRest_Data")
            if os.path.exists(os.path.join(fixed, "globalgamemanagers")):
                game_dir = fixed
                print(f"  (auto-corrected to {game_dir})")
        if not os.path.exists(os.path.join(game_dir, "globalgamemanagers")):
            print(f"\n[!] that path doesn't look like TravellersRest_Data —")
            print(f"    expected a 'globalgamemanagers' file inside it.")
            print(f"    double-check the path and try again.")
            sys.exit(1)
        os.environ["TR_GAME_DIR"] = game_dir
        print(f"  using: {game_dir}")

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
    print(f"  done!")
    print(f"{'='*60}\n")
    print(f"  to run the planner:")
    print(f"    python -m planner              (solo, localhost only)")
    print(f"    python -m planner --share       (LAN, friends on same WiFi)")
    print(f"    python -m planner --tunnel      (internet, anyone with the link)")
    print(f"")
    print(f"  for --tunnel you need a free ngrok account (one-time setup):")
    print(f"    1. sign up at https://ngrok.com")
    print(f"    2. copy your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken")
    print(f"    3. run: ngrok config add-authtoken YOUR_TOKEN")
    print(f"")
    print(f"  launching now...\n")

    subprocess.run([sys.executable, "-m", "planner"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\ncancelled")
    except Exception as e:
        print(f"\n\nerror: {e}")
        input("\npress enter to exit...")
