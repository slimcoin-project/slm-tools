# Slimcoin Tools

This repository should be used for miscellaneous tools and scripts.

# Tool list
## profitability.py

Calculates the probability to find Proof of Burn blocks, and the profitability of a burn investment. Work in progress.

**Basic Usage**:

  python3 profitability.py BURN_AMOUNT EFFECTIVEBURNCOINS

Without other options, this calculates the rough amount of blocks you will find in the next 365 days, if you burn BURN_AMOUNT, with certain default values. It creates a fake blockchain with the genesis block dating back to 2014-05-26, the birth date of Slimcoin, and assumes the average burn rate continues to be the same before and after your burn event. It also assumes that the average minting participation is 25% of all burnt coins (see below).

Other options can be consulted with the **--help** or **-h** option. You can, for example, change the time window you want to get the probability for (in days), change the average burn rate for the future blocks, measure the impact of an extraordinary large other burn transaction, or change the participation.

* You can get the current effectiveburncoins value from your Slimcoin client, typing *getburndata* in the Console or *slimcoind getburndata* for the command line daemon.
* Higher *effectiveburncoins* or *participation* values will result in a lower probability to find blocks.
* The *participation* default value of 0.25 is arbitrary and there is no research about it in Slimcoin. In (non-academic) attempts to measure this value in several PoS currencies, however, 25% was a typical value for participation.
