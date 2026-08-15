from datamodel import OrderDepth, TradingState, Order
from typing import Dict, List
import json

class Trader:
    def run(self, state: TradingState):
        result = {}
        trader_data = self.load_data(state.traderData)

        if "ASH_COATED_OSMIUM" in state.order_depths:
            result["ASH_COATED_OSMIUM"] = self.trade_ash_coated_osmium(state)

        if "INTARIAN_PEPPER_ROOT" in state.order_depths:
            result["INTARIAN_PEPPER_ROOT"] = self.trade_intarian_pepper_root(state)

        # Return the result dictionary, the required conversion value (0), and stringified state
        return result, 0, json.dumps(trader_data)

    def load_data(self, trader_data: str):
        if trader_data:
            try:
                return json.loads(trader_data)
            except:
                pass
        return {}

    def trade_ash_coated_osmium(self, state: TradingState) -> List[Order]:
        product = "ASH_COATED_OSMIUM"
        orders: List[Order] = []
        order_depth = state.order_depths[product]

        pos = state.position.get(product, 0)
        limit = 80
        fair = 10000
        quote_size = 12

        if not order_depth.buy_orders or not order_depth.sell_orders:
            return orders

        best_bid = max(order_depth.buy_orders.keys())
        best_ask = min(order_depth.sell_orders.keys())

        # Aggressive take - cross the spread if price is better than our static fair value
        for ask_price in sorted(order_depth.sell_orders.keys()):
            if ask_price < fair:
                ask_vol = -order_depth.sell_orders[ask_price]
                buy_qty = min(limit - pos, ask_vol)
                if buy_qty > 0:
                    orders.append(Order(product, ask_price, buy_qty))
                    pos += buy_qty
            else:
                break

        for bid_price in sorted(order_depth.buy_orders.keys(), reverse=True):
            if bid_price > fair:
                bid_vol = order_depth.buy_orders[bid_price]
                sell_qty = min(limit + pos, bid_vol)
                if sell_qty > 0:
                    orders.append(Order(product, bid_price, -sell_qty))
                    pos -= sell_qty
            else:
                break

        # Passive quoting - inventory skewing to manage risk
        skew = pos // 20
        bid_px = min(best_bid + 1, fair - 1 - skew)
        ask_px = max(best_ask - 1, fair + 1 - skew)

        if bid_px < ask_px:
            buy_qty = min(limit - pos, quote_size)
            sell_qty = min(limit + pos, quote_size)

            if buy_qty > 0:
                orders.append(Order(product, bid_px, buy_qty))
            if sell_qty > 0:
                orders.append(Order(product, ask_px, -sell_qty))

        return orders

    def trade_intarian_pepper_root(self, state: TradingState) -> List[Order]:
        product = "INTARIAN_PEPPER_ROOT"
        orders: List[Order] = []
        
        order_depth = state.order_depths[product]
        pos = state.position.get(product, 0)
        POSITION_LIMIT = 80
        
        # Pure Buy & Hold - No sell phase needed due to Mark-to-Market settlement
        if pos < POSITION_LIMIT and len(order_depth.sell_orders) > 0:
            for ask_price, ask_vol in sorted(order_depth.sell_orders.items()):
                available_vol = -ask_vol 
                buy_qty = min(POSITION_LIMIT - pos, available_vol)
                
                if buy_qty > 0:
                    orders.append(Order(product, ask_price, buy_qty))
                    pos += buy_qty
                
                if pos >= POSITION_LIMIT:
                    break

        return orders