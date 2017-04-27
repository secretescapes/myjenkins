import click


def positive_nonzero(ctx, param, value):
    if value <= 0:
        raise click.BadParameter('must be positive and non-zero')

    return value
