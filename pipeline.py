import argparse
import logging
from typing import Tuple, Optional, TypeVar

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions


T = TypeVar('T')


@beam.typehints.with_input_types(element=T, duration=float,
                                 variation=Optional[Tuple[float, float]])
@beam.typehints.with_output_types(T)
class SleepFn(beam.DoFn):
    def process(self, element, duration=0.5, variation=None, **kwargs):
        import time
        import random
        if variation:
            duration += random.uniform(*variation)
        time.sleep(duration)
        yield element


def main(options=None):
    with beam.Pipeline(options=options) as pipe:
        (
            pipe
            | 'Init' >> beam.Create(range(10))
            | 'Sleep' >> beam.ParDo(SleepFn(), duration=1.0)
            | 'Log' >> beam.Map(print)
        )


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser()
    _, args = parser.parse_known_args()
    options = PipelineOptions(args)
    main(options=options)
