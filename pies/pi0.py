# /// script
# requires-python = ">=3.9"
# description = "Smoke test script to try out on our raspberry pies. Blinks led a couple of times."
# dependencies = [
#     "gpiohero"
# ]
#
# [tool.uv.sources]
# gpiohero = { git = "https://github.com/cetkovicaleksa/justkeeplivin.git", subdirectory = "gpiohero", rev = "8beb9fc" }
# ///

import argparse
import logging

logging.basicConfig(
        level=logging.INFO,
        format= "%(name)s %(message)s",
    )

logger = logging.getLogger()


def main():
    parser = argparse.ArgumentParser(description="LED blinking example script.")
    parser.add_argument('-s', '--simulate', action='store_true', help="Simulate the blinking LED.")
    parser.add_argument('-p', '--pin', type=str, default=None, help="Gpio pin for the LED. Not required if simulated.")
    parser.add_argument('-t', '--times', type=int, default=3, help="Number of times to blink the LED. Default is 3.")

    args = parser.parse_args()

    if args.simulate:
        from gpiohero.sim import LED
        logger.info("Simulating LED.")
    else:
        if not args.pin:
            logger.error("Pin must be specified when using legit LED.")
            return
        
        from gpiohero.legit import LED
        logger.info("Using legit LED.")

    led = None
    try:
        led = LED(pin=str(args.pin or 0).upper())
        logger.info("Blinking LED@%s %d times.", led.pin, args.times)
        led.blink(n=args.times, background=False)
    except Exception as e: # don't have exceptions defined in gpiohero :(
        logger.error("Invalid pin: %s", e)
    finally:
        if led: 
            led.close()


if __name__ == '__main__':
    main()
