# Full Bug Fix Plan

## Goal
Fix all bugs so the bot works for new users (especially `/start`), all features work without crashes, and code quality is improved.

## Steps

### 1. CRITICAL: /start blocked by IsCheckSubChannels filter
- **File:** `filterss/check_sub_channel.py`
- **Changes:**
  1. Add `if message.text and message.text.startswith("/start"): return False` at top of `__call__`
  2. Replace `except:` with `except Exception:`
- **Why:** New user sends /start → filter returns True → handler consumes update → `CommandStart()` never fires

### 2. CRITICAL: Import premium_handler
- **File:** `handlers/users/__init__.py`
- **Changes:** Add `from . import premium_handler` (uncommented)
- **Why:** Premium nick/font handlers are never registered → crash when user clicks premium features

### 3. CRITICAL: Fix MockMessage missing answer()
- **File:** `handlers/users/menu_navigation.py`
- **Changes:** Add `answer()`, `answer_photo()`, `reply()` methods to `MockMessage` class
- **Why:** Premium navigation creates MockMessage → calls `message.answer()` → `AttributeError`

### 4. CRITICAL: time.sleep blocks event loop
- **File:** `handlers/users/admin.py`
- **Changes:** Replace `time.sleep(0.01)` with `await asyncio.sleep(0.01)`, add `import asyncio`
- **Why:** Blocking call freezes entire bot during ad broadcast

### 5. MODERATE: Remove /start check from kanalga_obuna handler body
- **File:** `handlers/users/admin.py`
- **Changes:** Remove the `/start` early-return block from `kanalga_obuna` (now handled by filter)
- **Why:** Redundant code, filter already handles it

### 6. MODERATE: Fix finally state clear on failure
- **File:** `handlers/users/admin.py`
- **Changes:** Remove `finally: await state.clear()`, move `state.clear()` to success path only
- **Why:** Currently clears state even on error → user must restart from scratch

### 7. MODERATE: Add multi-language support for games
- **File:** `handlers/users/games_system.py`
- **Changes:** Add `"us"` and `"ru"` translations to `game_texts`, use `language` parameter
- **Why:** Game buttons always show Uzbek regardless of user language

### 8. MODERATE: Fix password generator trapped state
- **File:** `handlers/users/password_generator.py`
- **Changes:** 
  1. After generating password, use `await state.clear()` instead of re-setting `WaitingForBase`
  2. Add feedback message for silent returns (emoji/command ignored)
- **Why:** User gets stuck in password mode with no escape

### 9. MODERATE: Fix add_user full_name not updated
- **File:** `baza/sqlite.py`
- **Changes:** Add `full_name=excluded.full_name` to ON CONFLICT UPDATE SET clause
- **Why:** User changes name in Telegram → DB still has old name forever

### 10. MODERATE: Centralize languages.json loading
- **File:** Create `loader.py` or use existing `loader.py`
- **Changes:** Load once at startup, import everywhere
- **Why:** 11 separate file reads at import time

### 11. MINOR: SQLite improvements
- **File:** `baza/sqlite.py`
- **Changes:**
  1. Change `telegram_id NUMBER` → `telegram_id INTEGER`
  2. Add `try/finally` to ensure `connection.close()` on exception
  3. Add `delete_user(telegram_id)` method
- **Why:** Code quality, robustness

### 12. MINOR: Fix trend.py typos
- **File:** `handlers/users/trend.py`
- **Changes:** Fix `get_pagination_keyboardd` → `get_pagination_keyboard`, deduplicate imports
- **Why:** Code quality

## Verification
After each step, restart bot and test:
1. New user /start → language selection → menu buttons
2. Existing user /start → menu buttons
3. Non-subscribed user clicks button → subscription message + Tekshirish button
4. Subscribed user → feature works
5. Admin /admin → channel management works
