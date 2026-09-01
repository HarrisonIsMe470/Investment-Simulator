"""
Game screens for Investment Simulator
Implements different UI screens for various game states
"""

import pygame
import math
from typing import Optional

from core.game import Game, GameState
from ui.dialogs import BuyDialog, SellDialog, NewsDetailDialog, OrderBookDialog
from ui.ui_manager import Screen, Colors, Button, Panel
from utils.config import ConfigManager


FONT_SCALE = float(ConfigManager().get("ui.font_scale", 1.15))


def ui_font(size: int, bold: bool = False):
    """Readable proportional UI font with broad platform fallbacks."""
    readable_size = max(13, round(size * FONT_SCALE))
    return pygame.font.SysFont("Arial,Helvetica,DejaVu Sans", readable_size, bold=bold)


def draw_label(surface, text, x, y, color=Colors.MUTED, size=13, bold=False):
    surface.blit(ui_font(size, bold).render(text, True, color), (x, y))


class MenuScreen(Screen):
    """Main menu screen."""
    
    def __init__(self, width: int, height: int, game: Game):
        """Initialize menu screen."""
        super().__init__(width, height)
        self.game = game
        
        # Create buttons
        button_y = height // 2 + 20
        self.new_game_btn = Button(width // 2 - 150, button_y, 300, 52, "START NEW RUN")
        self.load_game_btn = Button(width // 2 - 150, button_y + 66, 300, 52, "CONTINUE")
        self.quit_btn = Button(width // 2 - 150, button_y + 132, 300, 52, "EXIT")
        self.load_game_btn.color = Colors.LIGHT_GRAY
        self.quit_btn.color = Colors.SURFACE_ALT
        self.quit_btn.text_color = Colors.MUTED
        
        self.buttons = [self.new_game_btn, self.load_game_btn, self.quit_btn]
        self.status_message = ""
        self.animation_time = 0.0
    
    def handle_event(self, event: pygame.event.EventType) -> Optional[str]:
        """Handle events."""
        for button in self.buttons:
            if button.handle_event(event):
                if button == self.new_game_btn:
                    # Start new game
                    self.game.start_new_game("Player")
                    return "trading"
                elif button == self.load_game_btn:
                    success, self.status_message = self.game.load_latest_game()
                    return "trading" if success else None
                elif button == self.quit_btn:
                    return "quit"
        
        return None
    
    def update(self, dt: float):
        """Update screen."""
        self.animation_time += dt
    
    def draw(self) -> pygame.Surface:
        """Draw screen."""
        self.surface.fill(Colors.BLACK)
        for x in range(0, self.width, 32):
            pygame.draw.line(self.surface, (10, 17, 29), (x, 0), (x, self.height))
        for y in range(0, self.height, 32):
            pygame.draw.line(self.surface, (10, 17, 29), (0, y), (self.width, y))
        scan_y = int((self.animation_time * 38) % self.height)
        pygame.draw.line(self.surface, (18, 34, 54), (0, scan_y), (self.width, scan_y), 2)
        draw_label(self.surface, "NORTHSTAR FINANCIAL SYSTEMS  /  SIMULATION BUILD 1.0", 28, 24, Colors.MUTED, 12)
        font_large = ui_font(54, True)
        title = font_large.render("INVESTMENT", True, Colors.WHITE)
        title_rect = title.get_rect(center=(self.width // 2, 155))
        self.surface.blit(title, title_rect)
        glow = int(22 * (1 + math.sin(self.animation_time * 2.5)) / 2)
        title_color = tuple(min(255, c + glow) for c in Colors.CYAN)
        title2 = font_large.render("SIMULATOR", True, title_color)
        self.surface.blit(title2, title2.get_rect(center=(self.width // 2, 215)))
        font_small = ui_font(16)
        subtitle = font_small.render("365 DAYS  •  $10,000  •  TWO MOVES PER DAY", True, Colors.MUTED)
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, 274))
        self.surface.blit(subtitle, subtitle_rect)
        if self.status_message:
            status = ui_font(16, True).render(self.status_message, True, Colors.RED)
            self.surface.blit(status, status.get_rect(center=(self.width // 2, 325)))
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.surface, font_small)
        
        return self.surface


class TradingScreen(Screen):
    """Main trading screen."""
    
    def __init__(self, width: int, height: int, game: Game):
        """Initialize trading screen."""
        super().__init__(width, height)
        self.game = game

        # Panels
        self.info_panel = Panel(20, 18, width - 40, 64)
        self.market_panel = Panel(20, 98, 500, height - 118)
        self.portfolio_panel = Panel(540, 98, 360, 275)
        self.trading_panel = Panel(540, 391, 360, height - 411)
        self.email_panel = Panel(920, 98, width - 940, height - 118)

        # Buttons
        self.buy_btn = Button(558, 515, 150, 44, "BUY")
        self.sell_btn = Button(718, 515, 164, 44, "SELL")
        self.sell_btn.color = Colors.RED
        self.next_day_btn = Button(558, 574, 324, 46, "CLOSE DAY  →")
        self.next_day_btn.color = Colors.YELLOW
        self.portfolio_btn = Button(558, 635, 154, 38, "PORTFOLIO")
        self.portfolio_btn.color = Colors.LIGHT_GRAY
        self.save_btn = Button(722, 635, 160, 38, "SAVE GAME")
        self.save_btn.color = Colors.GREEN

        self.buy_dialog = BuyDialog(width, height, "AAPL", 0.0, 0.0, self._execute_buy)
        self.sell_dialog = SellDialog(width, height, "AAPL", 0.0, 0.0, self._execute_sell)
        self.status_message = "Ready to trade"
        self.selected_symbol = "AAPL"
        self.market_offset = 0
        self.news_dialog = None
        self.order_book_dialog = None
        self.option_underlying = None
        self.active_category = "all"
        self.category_filters = [
            ("ALL", "all"), ("STOCK", "stock"), ("OPTION", "options"),
            ("CRYPTO", "crypto"), ("BOND", "bond"), ("ETF", "etf"),
            ("FX", "forex"),
        ]
        self.last_stock_click_symbol = None
        self.last_stock_click_time = -1000
        self.animation_time = 0.0
        self.market_flash = 0.0

    def _filtered_symbols(self):
        symbols = self.game.market.get_available_symbols()
        if self.active_category == "options":
            if self.option_underlying is None:
                return self.game.market.get_option_underlyings()
            return self.game.market.get_option_chain(self.option_underlying, self.game.current_day)
        if self.active_category == "all":
            return symbols
        return [s for s in symbols if self.game.market.get_asset_type(s).value == self.active_category]

    def _ensure_game_started(self):
        """Create a new game if the player has not started one yet."""
        if self.game.portfolio is None:
            self.game.start_new_game("Player")

    def _execute_buy(self, symbol: str, quantity: float, price: float):
        """Execute a buy action and show feedback."""
        self._ensure_game_started()
        success, message = self.game.buy_asset(symbol, quantity, price)
        self.status_message = message

    def _execute_sell(self, symbol: str, quantity: float, price: float):
        """Execute a sell action and show feedback."""
        self._ensure_game_started()
        success, message = self.game.sell_asset(symbol, quantity, price)
        self.status_message = message

    def handle_event(self, event: pygame.event.EventType) -> Optional[str]:
        """Handle events."""
        # Dialogs are modal: no event may reach the dashboard behind them.
        if self.buy_dialog.is_visible():
            self.buy_dialog.handle_event(event)
            return None
        if self.sell_dialog.is_visible():
            self.sell_dialog.handle_event(event)
            return None
        if self.news_dialog and self.news_dialog.is_visible():
            self.news_dialog.handle_event(event)
            return None
        if self.order_book_dialog and self.order_book_dialog.is_visible():
            self.order_book_dialog.handle_event(event)
            return None
        if self.buy_btn.handle_event(event):
            if self.active_category == "options" and self.option_underlying is None:
                self.status_message = "Select a stock to open its option chain"
                return None
            self._ensure_game_started()
            symbol = self.selected_symbol
            price = self.game.market.get_price(symbol)
            multiplier = self.game.market.option_contracts.get(symbol, {}).get("multiplier", 1)
            self.buy_dialog = BuyDialog(
                self.width, self.height, symbol, price,
                self.game.portfolio.get_cash(), self._execute_buy, multiplier,
            )
            self.buy_dialog.show()
            self.status_message = f"Buying {symbol} at ${price:.2f}"
            return None
        elif self.sell_btn.handle_event(event):
            if self.active_category == "options" and self.option_underlying is None:
                self.status_message = "Select a stock to open its option chain"
                return None
            self._ensure_game_started()
            symbol = self.selected_symbol
            price = self.game.market.get_price(symbol)
            held = self.game.portfolio.get_position(symbol)
            quantity = held.quantity if held else 0.0
            self.sell_dialog = SellDialog(self.width, self.height, symbol, price, quantity, self._execute_sell)
            self.sell_dialog.show()
            self.status_message = f"Selling {symbol} at ${price:.2f}"
            return None
        elif self.next_day_btn.handle_event(event):
            self._ensure_game_started()
            _, self.status_message = self.game.advance_day()
            self.market_flash = 1.0
        elif self.portfolio_btn.handle_event(event):
            return "portfolio"
        elif self.save_btn.handle_event(event):
            _, self.status_message = self.game.save_game()

        # Market rows are selectable; the selected quote drives Buy/Sell.
        if event.type == pygame.MOUSEBUTTONDOWN and hasattr(event, "pos"):
            if event.button == 1:
                for index, (_, category) in enumerate(self.category_filters):
                    tab = pygame.Rect(34 + index * 58, 147, 54, 26)
                    if tab.collidepoint(event.pos):
                        self.active_category = category
                        if category == "options":
                            self.option_underlying = None
                        self.market_offset = 0
                        filtered = self._filtered_symbols()
                        if filtered:
                            self.selected_symbol = filtered[0]
                        self.status_message = f"Showing {category.upper()} instruments"
                        return None
            if event.button in (4, 5) and self.market_panel.rect.collidepoint(event.pos):
                direction = -1 if event.button == 4 else 1
                maximum = max(0, len(self._filtered_symbols()) - 12)
                self.market_offset = max(0, min(maximum, self.market_offset + direction * 5))
                return None
            if self.market_panel.rect.collidepoint(event.pos):
                row = (event.pos[1] - 211) // 34
                symbols = self._filtered_symbols()[self.market_offset:self.market_offset + 12]
                if 0 <= row < len(symbols):
                    if self.active_category == "options" and self.option_underlying is None:
                        self.option_underlying = symbols[row]
                        contracts = self._filtered_symbols()
                        if contracts:
                            self.selected_symbol = contracts[0]
                        self.market_offset = 0
                        self.status_message = f"Option chain: {symbols[row]}"
                        return None
                    self.selected_symbol = symbols[row]
                    self.status_message = f"Selected {self.selected_symbol}"
                    if event.button == 1 and self.game.market.get_asset_type(self.selected_symbol).value == "stock":
                        click_time = getattr(event, "timestamp", pygame.time.get_ticks())
                        is_double = (self.last_stock_click_symbol == self.selected_symbol and
                                     0 <= click_time - self.last_stock_click_time <= 450)
                        self.last_stock_click_symbol = self.selected_symbol
                        self.last_stock_click_time = click_time
                        if is_double:
                            book = self.game.market.get_order_book(self.selected_symbol)
                            self.order_book_dialog = OrderBookDialog(self.width, self.height, book)
                            self.order_book_dialog.show()
            if event.button == 1 and self.email_panel.rect.collidepoint(event.pos):
                row = (event.pos[1] - 157) // 78
                emails = list(reversed(self.game.email_system.get_all()))[:7]
                if 0 <= row < len(emails):
                    email = emails[row]
                    self.game.email_system.mark_as_read(email)
                    self.news_dialog = NewsDetailDialog(
                        self.width, self.height, email,
                        self.game.accept_offer, self.game.decline_offer
                    )
                    self.news_dialog.show()

        return None
    
    def update(self, dt: float):
        """Update screen."""
        self.animation_time += dt
        self.market_flash = max(0.0, self.market_flash - dt * 1.8)
        if self.buy_dialog.is_visible():
            self.buy_dialog.update(dt)
        if self.sell_dialog.is_visible():
            self.sell_dialog.update(dt)
        if self.news_dialog and self.news_dialog.is_visible():
            self.news_dialog.update(dt)
        if self.order_book_dialog and self.order_book_dialog.is_visible():
            self.order_book_dialog.update(dt)
    
    def draw(self) -> pygame.Surface:
        """Draw screen."""
        self.surface.fill(Colors.BLACK)
        font_small = ui_font(15)
        font_medium = ui_font(19, True)

        # Subtle moving scanline and grid keep the terminal visually alive.
        scan_y = int((self.animation_time * 46) % self.height)
        pygame.draw.line(self.surface, (18, 31, 49), (0, scan_y), (self.width, scan_y), 2)
        for x in range(0, self.width, 64):
            pygame.draw.line(self.surface, (9, 15, 26), (x, 0), (x, self.height))
        # Animated Metro transit line and station blocks.
        rail_y = self.height - 9
        pygame.draw.line(self.surface, Colors.METRO_BLUE, (20, rail_y), (self.width - 20, rail_y), 3)
        station_offset = int((self.animation_time * 70) % 90)
        metro_colors = (Colors.METRO_BLUE, Colors.METRO_ORANGE, Colors.GREEN, Colors.MAGENTA)
        for index, x in enumerate(range(-station_offset, self.width, 90)):
            pygame.draw.rect(self.surface, metro_colors[index % len(metro_colors)], (x, rail_y - 5, 13, 13))

        # Command bar
        self.info_panel.draw(self.surface)
        summary = self.game.get_game_summary()
        draw_label(self.surface, "INVESTMENT SIMULATOR", 38, 31, Colors.WHITE, 17, True)
        draw_label(self.surface, f"DAY {summary['current_day']:03d} / {self.game.GAME_DAYS}", 320, 33, Colors.CYAN, 14, True)
        draw_label(self.surface, "NET ASSETS", 505, 28, Colors.MUTED, 10)
        draw_label(self.surface, f"${summary['portfolio']['total_value']:,.2f}", 505, 43, Colors.WHITE, 16, True)
        draw_label(self.surface, "ACTIONS", 710, 28, Colors.MUTED, 10)
        actions_left = summary['max_operations_per_day'] - summary['operations_today']
        draw_label(self.surface, f"{actions_left} LEFT", 710, 43, Colors.YELLOW, 16, True)
        status_color = Colors.RED if any(word in self.status_message.lower() for word in ("cannot", "invalid", "insufficient", "maximum")) else Colors.GREEN
        status_pulse = 0.78 + 0.22 * (1 + math.sin(self.animation_time * 4)) / 2
        animated_status = tuple(int(channel * status_pulse) for channel in status_color)
        draw_label(self.surface, self.status_message[:42], 835, 39, animated_status, 12)

        # Market table
        self.market_panel.draw(self.surface)
        market_data = self.game.get_market_data()
        draw_label(self.surface, "MARKET WATCH", 38, 116, Colors.WHITE, 18, True)
        context_hint = (f"OPTIONS / {self.option_underlying} • click OPTION to go back"
                        if self.active_category == "options" and self.option_underlying
                        else "double-click a stock for market depth")
        draw_label(self.surface, context_hint, 235, 121, Colors.MUTED, 8)
        for index, (label, category) in enumerate(self.category_filters):
            tab = pygame.Rect(34 + index * 58, 147, 54, 26)
            active = category == self.active_category
            active_color = Colors.CYAN
            if active:
                glow = int(18 * (1 + math.sin(self.animation_time * 3)) / 2)
                active_color = tuple(min(255, c + glow) for c in Colors.CYAN)
            pygame.draw.rect(self.surface, active_color if active else Colors.SURFACE_ALT, tab, border_radius=4)
            text_color = Colors.BLACK if active else Colors.MUTED
            text = ui_font(8, True).render(label, True, text_color)
            self.surface.blit(text, text.get_rect(center=tab.center))
        draw_label(self.surface, "SYMBOL", 38, 188, Colors.MUTED, 10, True)
        draw_label(self.surface, "TYPE", 164, 188, Colors.MUTED, 10, True)
        draw_label(self.surface, "PRICE", 304, 188, Colors.MUTED, 10, True)
        draw_label(self.surface, "DAY", 440, 188, Colors.MUTED, 10, True)
        pygame.draw.line(self.surface, Colors.BORDER, (38, 207), (502, 207))
        y_pos = 218
        snapshot = self.game.market.get_snapshot()
        visible_symbols = self._filtered_symbols()[self.market_offset:self.market_offset + 12]
        for symbol in visible_symbols:
            price = market_data[symbol]
            change = snapshot[symbol]["change_percent"]
            selected = symbol == self.selected_symbol
            row_rect = pygame.Rect(30, y_pos - 7, 480, 32)
            if selected:
                pulse = int(10 * (1 + math.sin(self.animation_time * 5)) / 2)
                selected_bg = tuple(min(255, c + pulse) for c in Colors.SURFACE_ALT)
                pygame.draw.rect(self.surface, selected_bg, row_rect, border_radius=4)
                bar_width = 3 + int(2 * (1 + math.sin(self.animation_time * 5)) / 2)
                pygame.draw.rect(self.surface, Colors.CYAN, (30, y_pos - 7, bar_width, 32), border_radius=2)
            display_symbol = symbol
            if symbol in self.game.market.option_contracts:
                contract = self.game.market.option_contracts[symbol]
                display_symbol = f"{contract['kind'][0]} ${contract['strike']:g} D{contract['expiry_day']}"
            draw_label(self.surface, display_symbol, 42, y_pos, Colors.CYAN if selected else Colors.WHITE, 13, selected)
            if self.active_category == "options" and self.option_underlying is None:
                type_text = "OPTION CHAIN"
            else:
                type_text = snapshot[symbol]["asset_type"].upper()[:12]
            draw_label(self.surface, type_text, 164, y_pos, Colors.MUTED, 10)
            price_text = f"${price:,.4f}" if price < 10 else f"${price:,.2f}"
            price_color = Colors.YELLOW if self.market_flash > 0 else Colors.WHITE
            draw_label(self.surface, price_text, 304, y_pos, price_color, 12)
            draw_label(self.surface, f"{change:+.2f}%", 438, y_pos, Colors.GREEN if change >= 0 else Colors.RED, 11, True)
            y_pos += 34

        # Compact portfolio card
        self.portfolio_panel.draw(self.surface)
        positions = self.game.portfolio.get_all_positions() if self.game.portfolio else []
        draw_label(self.surface, "PORTFOLIO", 558, 116, Colors.WHITE, 18, True)
        draw_label(self.surface, f"CASH  ${summary['portfolio']['cash']:,.2f}", 558, 147, Colors.MUTED, 12)
        y_pos = 181
        for pos in positions[:4]:
            gain_color = Colors.GREEN if pos.unrealized_gain >= 0 else Colors.RED
            draw_label(self.surface, pos.symbol, 558, y_pos, Colors.WHITE, 12, True)
            draw_label(self.surface, f"{pos.quantity:g} units", 650, y_pos, Colors.MUTED, 11)
            draw_label(self.surface, f"${pos.total_value:,.2f}", 774, y_pos, gain_color, 11, True)
            y_pos += 38
        if not positions:
            draw_label(self.surface, "No positions yet", 558, y_pos, Colors.MUTED, 13)
            draw_label(self.surface, "Select a market row and place a trade.", 558, y_pos + 28, Colors.MUTED, 10)

        # Order ticket
        self.trading_panel.draw(self.surface)
        quote = snapshot[self.selected_symbol]
        draw_label(self.surface, "ORDER TICKET", 558, 409, Colors.WHITE, 18, True)
        draw_label(self.surface, self.selected_symbol, 558, 447, Colors.CYAN, 22, True)
        if quote["asset_type"] == "options":
            days_left = max(0, quote['expiry_day'] - self.game.current_day)
            detail = (f"{quote['kind']}  •  STRIKE ${quote['strike']:,.2f}  •  "
                      f"{days_left} DAYS  •  100 SHARES/CONTRACT")
        elif quote["asset_type"] == "bond":
            detail = f"3-MONTH SOVEREIGN BOND  •  {quote['maturity_days']}-DAY SELL LOCK"
        else:
            detail = quote["asset_type"].replace("_", " ").upper()
        draw_label(self.surface, detail, 558, 477, Colors.MUTED, 9)
        selected_price = quote["price"]
        draw_label(self.surface, f"${selected_price:,.4f}" if selected_price < 10 else f"${selected_price:,.2f}", 735, 447, Colors.WHITE, 20, True)
        for button in [self.buy_btn, self.sell_btn, self.next_day_btn, self.portfolio_btn, self.save_btn]:
            button.draw(self.surface, ui_font(12, True))

        # News wire
        self.email_panel.draw(self.surface)
        emails = list(reversed(self.game.email_system.get_all()))
        unread_count = len(self.game.email_system.get_unread())
        draw_label(self.surface, "NEWS WIRE", 938, 116, Colors.WHITE, 18, True)
        draw_label(self.surface, f"{unread_count} UNREAD", self.width - 102, 121, Colors.YELLOW, 10, True)
        if unread_count:
            radius = 3 + int(2 * (1 + math.sin(self.animation_time * 5)) / 2)
            pygame.draw.circle(self.surface, Colors.YELLOW, (self.width - 112, 129), radius)
        y_pos = 157
        for email in emails[:7]:
            tag_color = {"news": Colors.CYAN, "scam": Colors.RED, "ipo": Colors.MAGENTA, "report": Colors.GREEN}.get(email.email_type.value, Colors.YELLOW)
            draw_label(self.surface, email.email_type.value.upper(), 938, y_pos, tag_color, 9, True)
            words = email.subject.replace("📊", "").replace("🏆", "").strip()
            headline_color = Colors.WHITE if not email.read else Colors.MUTED
            draw_label(self.surface, words[:30], 938, y_pos + 19, headline_color, 11, not email.read)
            draw_label(self.surface, email.content[:42], 938, y_pos + 39, Colors.MUTED, 9)
            pygame.draw.line(self.surface, Colors.BORDER, (938, y_pos + 64), (self.width - 38, y_pos + 64))
            y_pos += 78
        if not emails:
            draw_label(self.surface, "Inbox zero.", 938, y_pos, Colors.MUTED, 12)

        if self.buy_dialog.is_visible():
            self.surface.blit(self.buy_dialog.draw(), (0, 0))
        if self.sell_dialog.is_visible():
            self.surface.blit(self.sell_dialog.draw(), (0, 0))
        if self.news_dialog and self.news_dialog.is_visible():
            self.surface.blit(self.news_dialog.draw(), (0, 0))
        if self.order_book_dialog and self.order_book_dialog.is_visible():
            self.surface.blit(self.order_book_dialog.draw(), (0, 0))

        return self.surface


class PortfolioScreen(Screen):
    """Detailed portfolio screen."""
    
    def __init__(self, width: int, height: int, game: Game):
        """Initialize portfolio screen."""
        super().__init__(width, height)
        self.game = game
        
        # Back button
        self.back_btn = Button(10, 10, 100, 40, "BACK")
        self.animation_time = 0.0
    
    def handle_event(self, event: pygame.event.EventType) -> Optional[str]:
        """Handle events."""
        if self.back_btn.handle_event(event):
            return "trading"
        
        return None
    
    def update(self, dt: float):
        """Update screen."""
        self.animation_time += dt
    
    def draw(self) -> pygame.Surface:
        """Draw screen."""
        self.surface.fill(Colors.BLACK)
        scan_y = int((self.animation_time * 42) % self.height)
        pygame.draw.line(self.surface, (18, 31, 49), (0, scan_y), (self.width, scan_y), 2)
        summary = self.game.get_game_summary()
        portfolio = summary['portfolio']
        header = Panel(20, 18, self.width - 40, 70)
        header.draw(self.surface)
        draw_label(self.surface, "PORTFOLIO OVERVIEW", 140, 38, Colors.WHITE, 20, True)
        draw_label(self.surface, f"DAY {summary['current_day']:03d}", self.width - 130, 44, Colors.CYAN, 13, True)
        self.back_btn.rect.topleft = (36, 33)
        self.back_btn.draw(self.surface, ui_font(11, True))

        metrics = [
            ("NET ASSETS", f"${portfolio['total_value']:,.2f}", Colors.WHITE),
            ("AVAILABLE CASH", f"${portfolio['cash']:,.2f}", Colors.CYAN),
            ("INVESTED", f"${portfolio['holdings_value']:,.2f}", Colors.MAGENTA),
            ("TOTAL RETURN", f"{portfolio['total_gain_percent']:+.2f}%", Colors.GREEN if portfolio['total_gain'] >= 0 else Colors.RED),
        ]
        card_width = (self.width - 100) // 4
        for index, (label, value, color) in enumerate(metrics):
            x = 20 + index * (card_width + 20)
            Panel(x, 108, card_width, 112).draw(self.surface)
            draw_label(self.surface, label, x + 18, 130, Colors.MUTED, 10, True)
            draw_label(self.surface, value, x + 18, 164, color, 20, True)

        table = Panel(20, 240, self.width - 40, self.height - 260)
        table.draw(self.surface)
        draw_label(self.surface, "OPEN POSITIONS", 40, 260, Colors.WHITE, 17, True)
        columns = [("SYMBOL", 40), ("CATEGORY", 200), ("QUANTITY", 380), ("AVG COST", 550), ("LAST PRICE", 735), ("VALUE", 920), ("RETURN", 1090)]
        for label, x in columns:
            draw_label(self.surface, label, x, 304, Colors.MUTED, 10, True)
        pygame.draw.line(self.surface, Colors.BORDER, (40, 326), (self.width - 40, 326))
        positions = self.game.portfolio.get_all_positions() if self.game.portfolio else []
        y_pos = 346
        if not positions:
            draw_label(self.surface, "No active positions", 40, y_pos, Colors.MUTED, 13)
        else:
            for pos in positions[:9]:
                gain_color = Colors.GREEN if pos.unrealized_gain >= 0 else Colors.RED
                values = [
                    (pos.symbol, 40, Colors.WHITE), (pos.asset_type.upper(), 200, Colors.MUTED),
                    (f"{pos.quantity:g}", 380, Colors.WHITE), (f"${pos.average_buy_price:,.2f}", 550, Colors.WHITE),
                    (f"${pos.current_price:,.2f}", 735, Colors.WHITE), (f"${pos.total_value:,.2f}", 920, Colors.WHITE),
                    (f"{pos.unrealized_gain_percent:+.2f}%", 1090, gain_color),
                ]
                for value, x, color in values:
                    draw_label(self.surface, value, x, y_pos, color, 12, value == pos.symbol)
                pygame.draw.line(self.surface, (27, 38, 57), (40, y_pos + 28), (self.width - 40, y_pos + 28))
                y_pos += 42

        return self.surface
