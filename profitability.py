# this script uses parts of the original Slimcoin code (/src/simulations/pob_difficulty.py)
# (c) The Slimcoin Developers 2014-19
# MIT License

from random import random as rand_num
import math, argparse, datetime

#constants for block types
#do we need to compute also POS blocks? (their difficulty could be ignored probably)
#TODO: Reward calculation
#TODO: Effect of participation on short-term profitability - should only be relevant if changes sharply.


POW = 0
POB = 1
POW_PROBABILITY = 0.8
POB_TARGET = 3
BURN_DECAY_RATE = 1.00000198 # original Slimcoin value.
POWPOB_BLOCKS_PER_DAY = 96
GENESIS_BLOCK_DATE = datetime.date(2014, 5, 28) # day of SLM inception

# default range for burn values
DEFAULT_POB_RANGE = 10000

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


## tool functions for CBlock class

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

    # TODO: Find out if 0 is the really correct value when still no coins were burnt (near genesis block).

    if total_coins_burned > 0:
        burn_adjust = cur_blk_coins_burned / total_coins_burned
    else:
        burn_adjust = 0

    last_diff = blocks[-1].diff
    new_diff = last_diff * (1 + adjust - burn_adjust)

    return new_diff

## small new functions

def reset_blocks():
    CBlock.blocks = []
    CBlock.ebc = 0
    CBlock.total_coins_burned = 0

def get_days_since_inception():
    today = datetime.date.today()
    timedelta = today - GENESIS_BLOCK_DATE
    return timedelta.days

def randomize_burns(avg_coins_burned, pob_range=DEFAULT_POB_RANGE):

    # this checks the last 1000 burn transactions and only allows a high
    # burn tx when the average of the last blocks was lower than avg_coins_burned
    blockheight = len(CBlock.blocks)
    begin_sequence = max(0, blockheight - 1000) # cannot become negative
    last_1000_burns = sum([ block.coins_burned for block in CBlock.blocks[begin_sequence:blockheight] ])

    rawburn = max(0, avg_coins_burned + (rand_num()-0.5) * pob_range)

    if last_1000_burns / (blockheight - begin_sequence) > avg_coins_burned:
        if rawburn > avg_coins_burned:
            burn_value = 0
        else:
            burn_value = rawburn
            
    else:
        burn_value = rawburn

    if burn_value > 0: # for debugging
        print(blockheight, burn_value)

    return burn_value
    
    

def print_intro(p):
    print("Calculating probabilities for the following scenario:")
    print("- Burnt amount:", p.burnt_amount)
    print("- nEffectiveBurnCoins:", p.neffectiveburncoins)
    if p.days_before and not p.blocks_before:
        print("- Days before burn transaction:", p.days_before)
    if p.days_after and not p.blocks_after:
        print("- Days generated after burn transaction:", p.days_after)
    if p.blocks_before:
        print("- Blocks generated before burn transaction:", p.blocks_before)
    if p.blocks_after:
        print("- Blocks generated after burn transaction:", p.blocks_after)
    if p.average_burn_rate:
        print("- Average burn rate: %f coins per PoB/PoW block." % p. average_burn_rate)
    if p.burn_event:
        print("- Another burn event of %f coins" % p.burn_event)
    if p.burn_event_blocks:
        print("  at %f blocks in the future" % p.burn_event_blocks)
        
        
 

## main loops


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
           
           coins_burned = randomize_burns(avg_coins_burned, pob_range)
        else:
           coins_burned = avg_coins_burned

        if rand_num() < multi * POW_PROBABILITY or blocks[-1].type == POB:         #make a PoW block
            blocks.append(CBlock(POW, coins_burned))
        else:                        #make a PoB block
            blocks.append(CBlock(POB, coins_burned))

    if verbose:
        for block in blocks:
            block.print_self()


def create_block_sequence(blocksbefore=0, ebc=0, blocksafter=0, ownburn=0, otherburn=0, otherburnblock=None, avg_coins_burned=None, randomize=True, reset=True, verbose=False, pob_range=None):

    if reset:
        reset_blocks()

    # first, generate all blocks until "now".
    # calculate average burn from ebc (nEffectiveBurnCoins) value.
    # Note: Real proportion of PoB/PoW blocks seems to be around 0.77, not 0.8.
    if blocksbefore > 0:
        
        est_pow_blocks_before = blocksbefore * 0.77 # * POW_PROBABILITY # estimated value, real value comes after avg burn.
        avg_decay = BURN_DECAY_RATE ** (est_pow_blocks_before / 2)
        avg_burn_before = (ebc / blocksbefore) * avg_decay
        
        gen_fake_blocks(blocksbefore, avg_coins_burned=avg_burn_before)

        # uncomment following lines for debugging:
        # print(avg_burn_before)
        # print(est_pow_blocks_before)
        # powbl = len([b for b in CBlock.blocks if b.type == POW])
        # allbl = len(CBlock.blocks)
        # print("Real proportion", powbl / allbl)
        # print(allbl, blocksbefore)
        


    # if avg_coins_burned is not given, then we use the value derived from nEffectiveBurnCoins we used for older blocks.
    if not avg_coins_burned:
        if avg_burn_before:
            avg_coins_burned = avg_burn_before
        else:
            avg_coins_burned = 0

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
    pow_blocks_after_burn = 0

    for block in CBlock.blocks[ownburn_blockheight:]:

        if block.type == POB: # you don't get PoB rewards for PoW blocks.

            total_ebc = block.ebc * participation
            own_ebc = ownburn / (BURN_DECAY_RATE ** pow_blocks_after_burn)
            probability = own_ebc / total_ebc
            expected_probabilities.append(probability)

        elif block.type == POW:
            pow_blocks_after_burn += 1 #only pow blocks lead to decay.

        if verbose:
            block.print_self()
            if block.type == POB:
                print("Own Effective Burnt Coins: %f" % own_ebc)
                print("Real Effective Burnt Coins with participation %f: %f" % (participation, total_ebc))
                print("Block find probability: %f" % probability)

    if printresult:
        print("=" * 30)
        initial_ebc = CBlock.blocks[ownburn_blockheight-1].ebc
        probsum = sum(expected_probabilities)
        pobblocks = len(expected_probabilities) # should give the correct number after the loop
        print("Result for %f burnt coins at %f nEffectiveBurnCoins and %f mint participation" % (ownburn, initial_ebc, participation))
        print("Expected found blocks (from %i PoB blocks)\n(sum of all probabilities): %f" % (pobblocks, probsum))

    return expected_probabilities

def get_probability(blocksbefore=0, ebc=0, blocksafter=0, daysbefore=None, daysafter=None, ownburn=0, otherburn=0, otherburnblock=None, avg_coins_burned=None, randomize=True, reset=True, verbose=False, pob_range=None, participation=0.2, printresult=True):

    if not blocksbefore:
        blocksbefore = POWPOB_BLOCKS_PER_DAY * daysbefore
    if not blocksafter:
        blocksafter = POWPOB_BLOCKS_PER_DAY * daysafter

    create_block_sequence(blocksbefore, ebc, blocksafter, ownburn, otherburn, otherburnblock, avg_coins_burned, randomize, reset=True, verbose=False, pob_range=pob_range)

    return calc_probabilities(ownburn_blockheight=blocksbefore + 1, ownburn=ownburn, participation=participation, verbose=verbose, printresult=printresult)

def cli():
    helptext_daysbefore = 'Generate blocks for X days before the burn transaction. Default is since the time of the coin inception (%s)' % GENESIS_BLOCK_DATE.strftime("%Y-%m-%d")
    days_since_inception = get_days_since_inception()

    parser = argparse.ArgumentParser(description="Profitability calculator.")
    parser.add_argument('burnt_amount', help='Amount of the burn transaction.', type=float)
    parser.add_argument('neffectiveburncoins', help='Effective burn coins at the moment of the burn.', type=float)
    parser.add_argument('-da', '--days-after', help='Generate blocks for X days after burn transaction. Default is one year (365 days).', type=int, default=365)
    parser.add_argument('-db', '--days-before', help=helptext_daysbefore, type=int, default=days_since_inception)
    
    # advanced arguments
    parser.add_argument('-bb', '--blocks-before', help='Generate X PoW/PoB blocks before the burn transaction. (Note: PoS blocks are ignored.)', type=int)
    parser.add_argument('-ba', '--blocks-after', help='Generate X PoW/PoB blocks after the burn transaction.', type=int)
    parser.add_argument('-e', '--burn-event', help='Add one other significant burn transaction with amount X in the future. This allows to calculate the impact of a large burn transaction.', type=float)
    parser.add_argument('-eb', '--burn-event-blocks', help='Blocks in the future the burn event will occur. By default, it is the next block after the own burn transaction.', type=int)
    parser.add_argument('-p', '--participation', help='Burning participation. Part of the coins which are effectively participating in burning (values from 0 to 1, default: 0.25).', type=float, default=0.25)
    parser.add_argument('-a', '--average-burn-rate', help='Average burning rate per PoW/PoB block. As a default, the average of the blocks preceding the burn transaction (derived from EffectiveBurnCoins) will be used.', type=float)
    parser.add_argument('-r', '--randomize', help='Add some randomness to the average burn transactions.', action='store_true')
    parser.add_argument('-g', '--range', help='Range for the randomness, in coins.', type=float)
    parser.add_argument('-v', '--verbose', help='Verbose mode. Will show all blocks with data.', action='store_true')
    parser.add_argument('-s', '--silent', help='Silent mode. Will only return probabilities (to use in scripts).', action='store_true')


    return parser.parse_args()
    



if __name__ == "__main__":

    p = cli()

    if p.silent == False:
        printresult = True
        print_intro(p)
    else:
        printresult = False
        
      

    get_probability(blocksbefore=p.blocks_before, ebc=p.neffectiveburncoins, blocksafter=p.blocks_after, daysbefore=p.days_before, daysafter=p.days_after, ownburn=p.burnt_amount, otherburn=p.burn_event, otherburnblock=p.burn_event_blocks, avg_coins_burned=p.average_burn_rate, randomize=p.randomize, verbose=p.verbose, pob_range=p.range, participation=p.participation, printresult=printresult)

