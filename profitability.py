# this script uses parts of the original Slimcoin code (/src/simulations/pob_difficulty.py)
# (c) The Slimcoin Developers 2014-19
# MIT License

from random import random as rand_num
import math, argparse

#constants for block types
#do we need to compute also POS blocks? (their difficulty could be ignored probably)
#TODO: Reward calculation
#TODO: Has participation an effect on difficulty? (I think: only if it changes rapidly.)


POW = 0
POB = 1
POW_PROBABILITY = 0.8
POB_TARGET = 3 # ???
BURN_DECAY_RATE = 1.00000198 # original Slimcoin value.
POWPOB_BLOCKS_PER_DAY = 96

# default range for burn values
DEFAULT_POB_RANGE = 10000

# check! Probably we don't need that.
# blocks = []
# total_coins_burned = 0

class CBlock:
    total_coins_burned = 0
    ebc = 0 # nEffectiveBurnCoins
    blocks = []
 
    def __init__(self, block_type, coins_burned=0):
        # be careful that blocks MUST be generated ALWAYS in strict sequential order for this to work.
        # self.coins_burned = 10000 * rand_num() # replaced, as we want to know what happens with different values.

        self.blockheight = len(CBlock.blocks)
        self.coins_burned = coins_burned
        self.type = block_type
        self.diff = calc_PoB_difficulty(self.coins_burned)

        CBlock.total_coins_burned += self.coins_burned
        self.total_coins_until_now = CBlock.total_coins_burned

        # Effective Burn Coins: burnt coins only decay on PoW blocks.
        # original: pindexPrev->nEffectiveBurnCoins / BURN_DECAY_RATE) + nBurnedCoins

        if self.type == POW:
            CBlock.ebc /= BURN_DECAY_RATE

        CBlock.ebc += self.coins_burned
        self.ebc = CBlock.ebc

    def print_self(self):

        print("Block: %d" % self.blockheight)
        if self.type == POW:
            print("Type: POW")
        elif self.type == POB:
            print("Type: POB")
        else:
            print("Type: Unknown")

        print("Coins Burned: %f" % self.coins_burned)

        print("Difficulty: %d" % self.diff)

        print("nEffectiveBurnCoins: %f" % self.ebc)

        print("Total Coins Burned: %f" % self.total_coins_until_now)

        print("-" * 30)


def PoW_blocks_back(): # modified to take "blocks" value (should not be global).
    # calculates how many blocks back from now were PoW.
    blocks = CBlock.blocks
    nPoW = 0
    i = -1

    if len(blocks) == 0:
        return nPoW

    while True:
        if i == -1 * len(blocks) - 1 or blocks[i].type == POB:
            break
        
        nPoW += 1
        i -= 1

    return nPoW

def logistic_curve(x):
    return (2 / (1 + math.e ** (-0.2 * x))) - 1

def calc_PoB_difficulty(cur_blk_coins_burned):
    #genesis block
    blocks = CBlock.blocks
    total_coins_burned = CBlock.total_coins_burned

    if len(blocks) == 0:
        return 10000

    nPoW = PoW_blocks_back()
    offset = POB_TARGET - nPoW

    #offset > 0, increas diff
    #offset < 0, decrease diff
    #offset == 0, do nothing

    adjust = logistic_curve(offset)

    # TODO: This doesn't look right with the division per zero.
    # Find out what total_coins_burned means.
    if total_coins_burned > 0:
        burn_adjust = cur_blk_coins_burned / total_coins_burned
    else:
        burn_adjust = 0

    last_diff = blocks[-1].diff
    new_diff = last_diff * (1 + adjust - burn_adjust)

    return new_diff

def reset_blocks():
    CBlock.blocks = []
    CBlock.ebc = 0
    CBlock.total_coins_burned = 0


def gen_fake_blocks(nBlocks, avg_coins_burned=0, pob_range=None, randomize=False, verbose=False, reset=False):
    # generate psuedo blocks randomly to fill the blocks list
    # new variable avg_coins_burned, which is the value passed to each block.

    if reset:
        reset_blocks()

    blocks = CBlock.blocks

    # genesis block
    # only added if this is the first function call
    if len(blocks) == 0:
        blocks.append(CBlock(POW))

    for n in range(nBlocks):
        multi = blocks[-1].diff / blocks[0].diff

        if randomize:
           if not pob_range:
               pob_range = DEFAULT_POB_RANGE
           
           coins_burned = max(0, avg_coins_burned + (rand_num()-0.5) * pob_range)
        else:
           coins_burned = avg_coins_burned

        if rand_num() < multi * POW_PROBABILITY or blocks[-1].type == POB:         #make a PoW block
            blocks.append(CBlock(POW, coins_burned))
        else:                        #make a PoB block
            blocks.append(CBlock(POB, coins_burned))

    if verbose:
        for block in blocks:
            block.print_self()




def create_block_sequence(blocksbefore=0, ebc=0, blocksafter=0, ownburn=0, otherburn=0, otherburnblock=None, avg_coins_burned=0, randomize=True, reset=True, verbose=False, pob_range=None):

    if reset:
        reset_blocks()

    # first, generate all blocks until "now".
    # calculate average burn from ebc (nEffectiveBurnCoins) value.
    avg_decay = BURN_DECAY_RATE ** (blocksbefore / 2)
    avg_burn_before = (ebc / blocksbefore) * avg_decay
    
    gen_fake_blocks(blocksbefore, avg_coins_burned=avg_burn_before)
    # last block before "now" gets the effectiveburncoins value.
    # This is easier/faster than to calculate the average burn value of each block, but has the same effect.
    # TODO: this is not working properly! Difficulty plummets to negative values.
    # if blocksbefore > 0:
    #    gen_fake_blocks(1, ebc)
    # now the block "now" where you burn.

    # if avg_coins_burned is not used, then we use the value derived from nEffectiveBurnCoins we used for older blocks.
    if not avg_coins_burned:
        avg_coins_burned = avg_burn_before

    gen_fake_blocks(1, avg_coins_burned=ownburn + avg_coins_burned, randomize=randomize, pob_range=pob_range)

    # blocks after: depend on otherburn/otherburnblock values
    if otherburn:
        if otherburnblock:
            gen_fake_blocks(otherburnblock - 1, avg_coins_burned=avg_coins_burned)
            blocksafter -= otherburnblock

        gen_fake_blocks(1, avg_coins_burned=avg_coins_burned + otherburn)

    gen_fake_blocks(blocksafter, avg_coins_burned=avg_coins_burned, randomize=randomize, pob_range=pob_range)

    if verbose:
        for block in CBlock.blocks:
            block.print_self()


def calc_probabilities(ownburn_blockheight, ownburn, participation, verbose=False, printresult=True):

    # loop from "now" on, past blocks are not needed in this loop.
    expected_probabilities = []

    for block in CBlock.blocks[ownburn_blockheight:]:

        effective_ebc = block.ebc * participation
        decay_blocks = block.blockheight - ownburn_blockheight
        own_ebc = ownburn / (BURN_DECAY_RATE ** decay_blocks)
        probability = own_ebc / effective_ebc
        expected_probabilities.append(probability)

        if verbose:
            block.print_self()
            print("Own Effective Burnt Coins: %f" % own_ebc)
            print("Real Effective Burnt Coins with participation %f: %f" % (participation, effective_ebc))
            print("Block find probability: %f" % probability)

    if printresult:
        print("=" * 30)
        initial_ebc = CBlock.blocks[ownburn_blockheight].ebc
        probsum = sum(expected_probabilities)
        blocksafter = decay_blocks # should give the correct number after the loop
        print("Result for %f burnt coins at %f nEffectiveBurnCoins and %f mint participation" % (ownburn, initial_ebc, participation))
        print("Expected found blocks (from %i)\n(sum of all probabilities): %f" % (blocksafter, probsum))

    return expected_probabilities

def get_probability(blocksbefore=0, ebc=0, blocksafter=0, daysbefore=None, daysafter=None, ownburn=0, otherburn=0, otherburnblock=None, avg_coins_burned=None, randomize=True, reset=True, verbose=False, pob_range=None, participation=0.2):

    if daysbefore:
        blocksbefore = POWPOB_BLOCKS_PER_DAY * daysbefore
    if daysafter:
        blocksafter = POWPOB_BLOCKS_PER_DAY * daysafter

    create_block_sequence(blocksbefore, ebc, blocksafter, ownburn, otherburn, otherburnblock, avg_coins_burned, randomize, reset=True, verbose=False, pob_range=pob_range)

    return calc_probabilities(ownburn_blockheight=blocksbefore + 1, ownburn=ownburn, participation=participation, verbose=verbose)

def cli():
    parser = argparse.ArgumentParser(description="Profitability calculator.")
    parser.add_argument('burnt_amount', help='Amount of the burn transaction.', type=float)
    parser.add_argument('neffectiveburncoins', help='Effective burn coins at the moment of the burn.', type=float)
    parser.add_argument('-db', '--days-before', help='Generate blocks for X days before the burn transaction.', type=int)
    parser.add_argument('-da', '--days-after', help='Generate blocks for X days after burn transaction.', type=int)
    
    # advanced arguments
    parser.add_argument('-bb', '--blocks-before', help='Generate X PoW/PoB blocks before the burn transaction. (Warning: PoS blocks are ignored.)', type=int)
    parser.add_argument('-ba', '--blocks-after', help='Generate X PoW/PoB blocks after the burn transaction.', type=int)
    parser.add_argument('-e', '--burn-event', help='Add one other significant burn transaction with amount X in the future. This allows to calculate the impact of a large burn transaction.', type=float)
    parser.add_argument('-eb', '--burn-event-blocks', help='Blocks in the future the burn event will occur. By default, it is the next block after the own burn transaction.', type=int)
    parser.add_argument('-p', '--participation', help='Burning participation. Part of the coins which are effectively participating in burning (values from 0 to 1, default: 0.2).', type=float, default=0.2)
    parser.add_argument('-a', '--average-burn-rate', help='Average burning rate per PoW/PoB block. As a default, the average of the blocks preceding the burn transaction (derived from EffectiveBurnCoins) will be used.', type=float)
    parser.add_argument('-r', '--randomize', help='Add some randomness to the average burn transactions.', type=bool)
    parser.add_argument('-g', '--range', help='Range for the randomness, in coins.', type=float)
    parser.add_argument('-v', '--verbose', help='Verbose mode. Will show all blocks with data.', action='store_true')


    return parser.parse_args()
    



if __name__ == "__main__":

    p = cli()

    get_probability(blocksbefore=p.blocks_before, ebc=p.neffectiveburncoins, blocksafter=p.blocks_after, daysbefore=p.days_before, daysafter=p.days_after, ownburn=p.burnt_amount, otherburn=p.burn_event, otherburnblock=p.burn_event_blocks, avg_coins_burned=p.average_burn_rate, randomize=p.randomize, verbose=p.verbose, pob_range=p.range, participation=p.participation)

