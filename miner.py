"""
PwnTensor subnet miner.

Registers an axon on the Bittensor network and serves game AI responses.
Receives GameStateSynapse from validators with game state, returns actions.

The miner's intelligence lives entirely inside the handler functions.
This baseline ships with simple scripted AI per game — miners replace
these with better strategies to earn higher weights.
"""

import os
import time
import click
import logging
import threading
import sys
import bittensor as bt
from bittensor_wallet import Wallet
from protocol import GameStateSynapse
from miner_ai import handle_game_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

HEARTBEAT_TIMEOUT = 600


def heartbeat_monitor(last_heartbeat, stop_event):
    while not stop_event.is_set():
        time.sleep(5)
        if time.time() - last_heartbeat[0] > HEARTBEAT_TIMEOUT:
            logger.error("No heartbeat in 600s. Restarting.")
            logging.shutdown(); os.execv(sys.executable, [sys.executable] + sys.argv)


def forward(synapse: GameStateSynapse) -> GameStateSynapse:
    """
    Main forward function — called by the axon when a validator sends
    a GameStateSynapse. Routes to the appropriate game handler.
    """
    action, action_args = handle_game_state(
        game_id=synapse.game_id,
        state=synapse.state,
        valid_actions=synapse.valid_actions,
        tick=synapse.tick,
        episode_seed=synapse.episode_seed,
    )
    synapse.action = action
    synapse.action_args = action_args
    return synapse


def blacklist(synapse: GameStateSynapse) -> tuple[bool, str]:
    """Reject requests from non-validators (no hotkey in metagraph)."""
    if synapse.dendrite.hotkey not in metagraph.hotkeys:
        return True, "Hotkey not in metagraph"
    uid = metagraph.hotkeys.index(synapse.dendrite.hotkey)
    if not metagraph.validator_permit[uid]:
        return True, "No validator permit"
    return False, ""


# Global metagraph reference for blacklist checks
metagraph = None


@click.command()
@click.option("--network", default=lambda: os.getenv("NETWORK", "finney"))
@click.option("--netuid", type=int, default=lambda: int(os.getenv("NETUID", "1")))
@click.option("--coldkey", default=lambda: os.getenv("WALLET_NAME", "default"))
@click.option("--hotkey", default=lambda: os.getenv("HOTKEY_NAME", "default"))
@click.option("--port", type=int, default=lambda: int(os.getenv("AXON_PORT", "8091")))
@click.option("--log-level", default=lambda: os.getenv("LOG_LEVEL", "INFO"))
def main(network: str, netuid: int, coldkey: str, hotkey: str, port: int, log_level: str):
    """Run the PwnTensor subnet miner."""
    global metagraph

    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    logger.info(f"Starting PwnTensor miner on network={network}, netuid={netuid}, port={port}")

    last_heartbeat = [time.time()]
    stop_event = threading.Event()
    heartbeat_thread = threading.Thread(
        target=heartbeat_monitor, args=(last_heartbeat, stop_event), daemon=True
    )
    heartbeat_thread.start()

    try:
        wallet = Wallet(name=coldkey, hotkey=hotkey)
        subtensor = bt.Subtensor(network=network)
        metagraph = bt.Metagraph(netuid=netuid, network=network)
        metagraph.sync(subtensor=subtensor)

        my_hotkey = wallet.hotkey.ss58_address
        if my_hotkey not in metagraph.hotkeys:
            logger.error(f"Hotkey {my_hotkey} not registered on netuid {netuid}")
            stop_event.set()
            return
        my_uid = metagraph.hotkeys.index(my_hotkey)
        logger.info(f"Miner UID: {my_uid}")

        # Set up axon
        axon = bt.axon(wallet=wallet, port=port)
        axon.attach(
            forward_fn=forward,
            blacklist_fn=blacklist,
        )
        axon.serve(netuid=netuid, subtensor=subtensor)
        axon.start()
        logger.info(f"Axon serving on port {port}")

        # Keep alive loop — sync metagraph periodically
        while True:
            try:
                last_heartbeat[0] = time.time()
                metagraph.sync(subtensor=subtensor)
                logger.debug(f"Metagraph synced: {metagraph.n} neurons")
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Miner stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in miner loop: {e}")
                time.sleep(12)

        axon.stop()
    finally:
        stop_event.set()
        heartbeat_thread.join(timeout=2)


if __name__ == "__main__":
    main()
