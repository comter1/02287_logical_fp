import random
from collections import defaultdict

# Initialize the deck
def initialize_game():
    deck = ['J', 'J', 'Q', 'Q', 'K', 'K']
    random.shuffle(deck)
    return deck

# Evaluate the strength of the hand and community card
def evaluate_hand(player_hand, community_card):
    if player_hand == community_card:
        return 4  # Pair
    return {'J': 1, 'Q': 2, 'K': 3}[player_hand]  # Strength of a single card

# Initialize strategies
def initialize_strategy():
    strategy_rewards = defaultdict(float)
    strategy_counts = defaultdict(int)
    return strategy_rewards, strategy_counts

# Choose a strategy
def choose_strategy(strategy_rewards, strategy_counts, epsilon=0.1):
    if random.random() < epsilon:
        return random.choice(['fold', 'call', 'raise', 'check'])
    else:
        avg_rewards = {action: strategy_rewards[action] / (strategy_counts[action] + 1e-5)
                       for action in ['fold', 'call', 'raise', 'check']}
        return max(avg_rewards, key=avg_rewards.get)

# Update strategy rewards
def update_strategy(strategy_rewards, strategy_counts, action, reward):
    strategy_rewards[action] += reward
    strategy_counts[action] += 1

# Classify actions into behavior categories
def classify_action(hand_strength, action):
    if hand_strength == 1:  # Weak hand
        if action == 'raise':
            return 'bluff'
        return 'truthful'
    elif hand_strength == 2:  # Medium-strength hand
        if action == 'call' or action == 'raise':
            return 'truthful'
        return 'slowplay'
    else:  # Strong hand
        if action == 'call':
            return 'slowplay'
        if action == 'raise':
            return 'truthful'
        return 'truthful'

# Betting round logic
def betting_round(players, pot, raise_amount, max_raises, community_card, strategies, phase):
    num_raises = 0
    current_bet = 1
    action_order = [1, 2]
    active_players = [pid for pid, p in players.items() if not p['folded']]
    strategy_log = {pid: [] for pid in players}
    behavior_log = {pid: [] for pid in players}

    # Reset current bets for all players
    for player in players.values():
        player['current_bet'] = 0

    while len(active_players) > 1:
        for player_id in action_order:
            player = players[player_id]
            if player['folded']:
                continue

            # Select an action using dynamic strategy
            strategy_rewards, strategy_counts = strategies[player_id]
            action = choose_strategy(strategy_rewards, strategy_counts)

            hand_strength = evaluate_hand(player['hand'], community_card)
            behavior = classify_action(hand_strength, action)
            behavior_log[player_id].append((action, behavior))

            strategy_log[player_id].append(action)

            if action == 'fold':
                player['folded'] = True
            elif action == 'call':
                to_call = current_bet - player['current_bet']
                if player['stack'] >= to_call:
                    player['stack'] -= to_call
                    player['current_bet'] += to_call
                    pot += to_call
                else:
                    player['folded'] = True  # Fold if they cannot afford the call
            elif action == 'raise' and num_raises < max_raises:
                to_raise = raise_amount + (current_bet - player['current_bet'])
                if player['stack'] >= to_raise:
                    player['stack'] -= to_raise
                    player['current_bet'] += to_raise
                    pot += to_raise
                    current_bet += raise_amount
                    num_raises += 1
                else:
                    player['folded'] = True  # Fold if they cannot afford the raise
            elif action == 'check':
                action_order.reverse()  # Swap first player advantage

            active_players = [pid for pid, p in players.items() if not p['folded']]
            if len(active_players) == 1:
                return pot, active_players[0], strategy_log, behavior_log

        # Check if the round is finished
        if all(p['current_bet'] == current_bet for p in players.values() if not p['folded']):
            break

    return pot, None, strategy_log, behavior_log

# Determine the winner
def determine_winner(players, community_card):
    active_players = [pid for pid, p in players.items() if not p['folded']]
    if len(active_players) == 1:
        return active_players[0]
    player_values = {pid: evaluate_hand(players[pid]['hand'], community_card) for pid in active_players}
    max_value = max(player_values.values())
    winners = [pid for pid, value in player_values.items() if value == max_value]
    return winners[0] if len(winners) == 1 else None

# Simulate a single game
def simulate_game(strategies):
    deck = initialize_game()
    players = {
        1: {'hand': None, 'stack': 800, 'current_bet': 1, 'folded': False},
        2: {'hand': None, 'stack': 800, 'current_bet': 1, 'folded': False},
    }
    pot = 2
    community_card = None

    # Deal hands to players
    for player in players.values():
        player['hand'] = deck.pop(0)
    community_card = deck.pop(0)

    # First betting round
    pot, winner, strategy_log1, behavior_log1 = betting_round(players, pot, 2, 2, None, strategies, "first")
    if winner:
        players[winner]['stack'] += pot  # Distribute chips
        return winner, pot, strategy_log1, behavior_log1

    # Second betting round
    pot, winner, strategy_log2, behavior_log2 = betting_round(players, pot, 4, 2, community_card, strategies, "second")
    if winner:
        players[winner]['stack'] += pot  # Distribute chips
        behavior_log1.update(behavior_log2)
        return winner, pot, strategy_log1, behavior_log1

    # Showdown phase
    winner = determine_winner(players, community_card)
    if winner:
        players[winner]['stack'] += pot  # Distribute chips
    behavior_log1.update(behavior_log2)
    return winner, pot, strategy_log1, behavior_log1

# Run multiple games
def monte_carlo_simulation(num_simulations=100):
    results = defaultdict(int)
    strategies = {
        1: initialize_strategy(),
        2: initialize_strategy()
    }
    behavior_summary = defaultdict(lambda: defaultdict(int))
    strategy_chips = defaultdict(lambda: defaultdict(int))

    for _ in range(num_simulations):
        winner, pot, strategy_log, behavior_log = simulate_game(strategies)
        results[winner] += pot

        # Update behavior statistics and strategy impact
        for player_id, actions in behavior_log.items():
            for action, behavior in actions:
                behavior_summary[player_id][behavior] += 1
                strategy_chips[player_id][behavior] += pot if player_id == winner else -pot

    return results, behavior_summary, strategy_chips

# Execute simulation
simulation_results, behavior_summary, strategy_chips = monte_carlo_simulation(100)

# Output results
print("Simulation Results:")
for player, winnings in simulation_results.items():
    print(f"Player {player}: {winnings} chips")

print("\nBehavior Summary:")
for player_id, behaviors in behavior_summary.items():
    print(f"Player {player_id}: {dict(behaviors)}")

print("\nStrategy Chips Summary:")
for player_id, chips in strategy_chips.items():
    print(f"Player {player_id}: {dict(chips)}")
