# Travellers Rest Planner - Absolute Beginner Install Guide

> **You will need:** A Windows PC with Travellers Rest installed on Steam, and about 15 minutes.
>
> **You do NOT need:** Any programming experience whatsoever.

---

## Step 1: Install Python

Python is the programming language this tool is written in. You need to install it so your computer can run it.

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.x.x"** button (whatever the latest version is).
3. **Run the installer.**
4. **⚠️ IMPORTANT: On the very first screen, check the box that says "Add python.exe to PATH."** This is the single most common mistake people make. If you skip this, nothing else will work.
5. Click **"Install Now"** and wait for it to finish.

### Verify it worked

1. Press `Win + R` on your keyboard, type `cmd`, and press Enter. A black window (the Command Prompt) will open.
2. Type the following and press Enter:

```
python --version
```

You should see something like `Python 3.12.4`. If you see an error instead, uninstall Python and redo Step 1, making sure you checked "Add to PATH."

---

## Step 2: Install Git

Git is a tool that lets you download code from GitHub (where this project lives).

1. Go to **https://git-scm.com/download/win**
2. The download should start automatically. Run the installer.
3. Click **Next** through everything, keeping all defaults. You don't need to change anything.

### Verify it worked

In your Command Prompt (open a new one if you closed it), type:

```
git --version
```

You should see something like `git version 2.44.0`. If you get an error, close and reopen Command Prompt and try again.

---

## Step 3: Download the Planner

Now you'll download the actual tool. In your Command Prompt, type these commands **one at a time**, pressing Enter after each:

```
cd Desktop
git clone https://github.com/truix/travellers-rest-planner.git
cd travellers-rest-planner
```

This creates a folder called `travellers-rest-planner` on your Desktop containing all the code.

---

## Step 4: Install the Planner's Dependencies

The planner uses some add-on libraries (think of them as plugins). One command installs all of them:

```
pip install -r requirements.txt
```

You'll see a bunch of text scroll by. Wait until it finishes and you get your cursor back. If you see "Successfully installed..." at the end, you're good.

**If you get an error about "pip not recognized":** Go back to Step 1. You probably forgot to check "Add to PATH."

---

## Step 5: Extract Your Game Data

For legal reasons, the planner doesn't include any of the game's files. Instead, it reads them from your own copy of Travellers Rest. Run these commands **one at a time**:

```
python scripts/dump_mono.py
python scripts/dump_i2l.py
python scripts/dump_icons.py
python scripts/dump_coins.py
python scripts/dump_hotspots.py
python scripts/dump_maps.py
python scripts/synthesize.py
```

Each one will take a few seconds to a few minutes. The map one (`dump_maps.py`) is the slowest at around 3 minutes.

**If you get an error about the game not being found:** Your Steam install might be in a non-default location. Run this command first (change the path to match where your game actually is):

```
set TR_GAME_DIR=D:\SteamLibrary\steamapps\common\Travellers Rest\Windows\TravellersRest_Data
```

Not sure where Steam put it? In Steam, right-click Travellers Rest, click **Properties**, then **Installed Files**, then **Browse**. Copy that folder path.

---

## Step 6: Run the Planner

```
python -m planner
```

Then open your web browser and go to:

**http://127.0.0.1:8765/**

That's it. The planner is now running. Leave the Command Prompt window open (closing it stops the planner).

The planner watches your save files in real time. Play the game, and every time it autosaves, the planner updates automatically.

---

## How to Run It Again Later

You don't need to repeat all the steps. Just:

1. Open Command Prompt
2. Type:

```
cd Desktop\travellers-rest-planner
python -m planner
```

3. Go to **http://127.0.0.1:8765/** in your browser.

You only need to re-run the `dump_*.py` extraction scripts if the game gets a major update.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` or `pip` is "not recognized" | Uninstall Python, reinstall it, and **check "Add to PATH"** this time. |
| `git` is "not recognized" | Close and reopen Command Prompt. If still broken, reinstall Git. |
| Extraction scripts say they can't find the game | Set `TR_GAME_DIR` to your game's data folder (see Step 5). |
| The browser page is blank or won't load | Make sure the Command Prompt window running the planner is still open. Check it for error messages. |
| `pip install` fails with a permission error | Try `pip install -r requirements.txt --user` instead. |
| Something else entirely | Open an issue on the [GitHub page](https://github.com/truix/travellers-rest-planner/issues) and paste the full error message. |

---

*Made with ☕ for the Travellers Rest community.*
