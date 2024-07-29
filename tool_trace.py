import click
from commands import calibrate, convert
import logging

logging.basicConfig(
   level=logging.DEBUG,
   format='%(message)s',
)
log = logging.getLogger(__name__)

@click.group(help="Tool to extract the outlines of tools")
def cli():
    pass

cli.add_command(calibrate.calibrate)
cli.add_command(convert.convert)

if __name__ == "__main__":
  cli()
