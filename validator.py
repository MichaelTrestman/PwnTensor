"""
PwnTensor subnet validator.

Each game on the subnet maps to a Bittensor incentive mechanism. The validator:
  1. Pulls the game registry (which games are active, which mechanism each maps to)
  2. For each game: runs headless sim episodes, fans out GameStateSynapse to miner
     axons, collects actions, steps the sim, scores episodes
  3. Sets weights per mechanism (each game's rank-normalized scores go to its
     own mechanism's set_weights call)
  4. Serves the frontend (live match spectating for all games: PacTensor, Melee Light, KAZ)
"""

import os
import time
import click
import logging
import threading
import sys
import bittensor as bt
from bittensor_wallet import Wallet
from game_registry import get_game_registry, get_games_by_mechanism
from reward import score_episode, rank_normalize

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

HEARTBEAT_TIMEOUT = 600  # seconds


def heartbeat_monitor(last_heartbeat, stop_event):
    while not stop_event.is_set():
        time.sleep(5)
        if time.time() - last_heartbeat[0] > HEARTBEAT_TIMEOUT:
            logger.error("No heartbeat detected in the last 600 seconds. Restarting process.")
            logging.shutdown(); os.execv(sys.executable, [sys.executable] + sys.argv)


@click.command()
@click.option(
    "--network",
    default=lambda: os.getenv("NETWORK", "finney"),
    help="Network to connect to (finney, test, local)",
)
@click.option(
    "--netuid",
    type=int,
    default=lambda: int(os.getenv("NETUID", "1")),
    help="Subnet netuid",
)
@click.option(
    "--coldkey",
    default=lambda: os.getenv("WALLET_NAME", "default"),
    help="Wallet name",
)
@click.option(
    "--hotkey",
    default=lambda: os.getenv("HOTKEY_NAME", "default"),
    help="Hotkey name",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default=lambda: os.getenv("LOG_LEVEL", "INFO"),
    help="Logging level",
)
def main(network: str, netuid: int, coldkey: str, hotkey: str, log_level: str):
    """Run the PwnTensor subnet validator."""
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    logger.info(f"Starting PwnTensor validator on network={network}, netuid={netuid}")

    # Heartbeat setup
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
        logger.info(f"Metagraph synced: {metagraph.n} neurons at block {metagraph.block}")

        my_hotkey = wallet.hotkey.ss58_address
        if my_hotkey not in metagraph.hotkeys:
            logger.error(f"Hotkey {my_hotkey} not registered on netuid {netuid}")
            stop_event.set()
            return
        my_uid = metagraph.hotkeys.index(my_hotkey)
        logger.info(f"Validator UID: {my_uid}")

        tempo = subtensor.get_subnet_hyperparameters(netuid).tempo
        logger.info(f"Subnet tempo: {tempo} blocks")

        # Load game registry — each game maps to a mechanism index
        games = get_game_registry()
        mechanism_indices = sorted(set(g.mechanism_index for g in games))
        logger.info(
            f"Game registry: {len(games)} games across mechanisms {mechanism_indices}"
        )
        for g in games:
            logger.info(f"  [{g.mechanism_index}] {g.game_id}: {g.name}")

        last_weight_block = 0

        # Main validator loop
        while True:
            try:
                metagraph.sync(subtensor=subtensor)
                current_block = subtensor.get_current_block()
                last_heartbeat[0] = time.time()

                blocks_since_last = current_block - last_weight_block
                if blocks_since_last >= tempo:
                    logger.info(f"Block {current_block}: Running episodes and setting weights")

                    # For each mechanism, run episodes for its games and set weights
                    for mech_idx in mechanism_indices:
                        mech_games = get_games_by_mechanism(mech_idx)
                        logger.info(
                            f"Mechanism {mech_idx}: "
                            f"{[g.game_id for g in mech_games]}"
                        )

                        # TODO: For each game in this mechanism:
                        #   1. Derive episode seed: hash(block_hash + my_hotkey + tick)
                        #   2. Initialize headless sim via game adapter
                        #   3. For each tick in the episode:
                        #      a. Build GameStateSynapse with current state
                        #      b. Fan out to all miner axons via dendrite
                        #      c. Collect action responses
                        #      d. Step the sim with each miner's action
                        #   4. Score each miner's episode with score_episode(game_id, log)
                        #   5. Rank-normalize scores across miners
                        #   6. Set weights for this mechanism:
                        #      subtensor.set_weights(
                        #          wallet=wallet, netuid=netuid,
                        #          uids=uids, weights=weights,
                        #          mechanism_id=mech_idx,
                        #      )

                        # Placeholder: burn to UID 0 per mechanism
                        uids = [0]
                        weights = [1.0]

                        success = subtensor.set_weights(
                            wallet=wallet,
                            netuid=netuid,
                            uids=uids,
                            weights=weights,
                            wait_for_inclusion=True,
                            wait_for_finalization=False,
                        )

                        if success:
                            logger.info(f"  Mechanism {mech_idx}: weights set")
                        else:
                            logger.warning(f"  Mechanism {mech_idx}: failed to set weights")

                    last_weight_block = current_block
                else:
                    logger.debug(
                        f"Block {current_block}: Waiting for tempo "
                        f"({blocks_since_last}/{tempo} blocks)"
                    )

                time.sleep(12)

            except KeyboardInterrupt:
                logger.info("Validator stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in validator loop: {e}")
                time.sleep(12)
    finally:
        stop_event.set()
        heartbeat_thread.join(timeout=2)


if __name__ == "__main__":
    main()
