# Source Generated with Decompyle++
# File: main.cpython-312.pyc (Python 3.12)

'''
CLI Entry Point for Synthetic Data Generator.

Provides the command-line interface for running the generator with
support for configuration overrides, seed setting, and various outputs.

Requirements: 12.2, 12.3, 12.4, 12.5
'''
from __future__ import annotations
import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from synthetic_generator.core.account_factory import AccountFactory
from synthetic_generator.core.seed_manager import SeedManager
from synthetic_generator.core.transaction_generator import TimeRange, TransactionGenerator
from synthetic_generator.evaluation.dataset_generator import EvaluationDatasetGenerator
from synthetic_generator.output.file_writer import FileWriter
from synthetic_generator.output.kafka_writer import KafkaWriter
from synthetic_generator.stats.collector import StatsCollector
from synthetic_generator.stats.reporter import output_stats_json, output_stats_text
logging.basicConfig(level = logging.INFO, format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt = '%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('synthetic_generator')

def setup_parser():
    '''Setup command line argument parser.'''
    parser = argparse.ArgumentParser(description = 'FundGuard Synthetic Data Generator for Anti-Money Laundering.')
    parser.add_argument('--mode', type = str, choices = [
        'evaluation',
        'custom'], default = 'evaluation', help = "Generation mode: 'evaluation' (1M txns, 2% fraud) or 'custom'.")
    parser.add_argument('--seed', type = int, default = 42, help = 'Master seed for reproducible generation (default: 42).')
    parser.add_argument('--count', type = int, default = 100000, help = 'Number of transactions to generate (for custom mode).')
    parser.add_argument('--accounts', type = int, default = 10000, help = 'Number of accounts in the pool.')
    parser.add_argument('--output-dir', type = str, default = 'data/output', help = 'Directory to save output files (CSV, Parquet, Stats).')
    parser.add_argument('--format', type = str, choices = [
        'csv',
        'parquet'], default = 'csv', help = 'Output file format.')
    parser.add_argument('--kafka', action = 'store_true', help = 'Stream output to Kafka.')
    parser.add_argument('--kafka-brokers', type = str, default = 'localhost:9092', help = 'Kafka bootstrap servers.')
    parser.add_argument('--kafka-topic', type = str, default = 'transactions', help = 'Kafka topic to stream to.')
    parser.add_argument('--kafka-tps', type = int, default = 1000, help = 'Kafka streaming rate (transactions per second).')
    return parser


def main():
    '''Main CLI entry point.'''
    parser = setup_parser()
    args = parser.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents = True, exist_ok = True)
    logger.info('============================================================')
    logger.info('FundGuard Synthetic Data Generator')
    logger.info('============================================================')
    logger.info('Mode: %s', args.mode)
    logger.info('Seed: %d', args.seed)
    logger.info('Output Dir: %s', out_dir.absolute())
    seed_manager = SeedManager(master_seed = args.seed)
    if args.mode == 'evaluation':
        logger.info('Running evaluation dataset generation (1M txns)...')
        generator = EvaluationDatasetGenerator(seed_manager)
        end = datetime.now()
        start = end - timedelta(days = 30)
        time_range = TimeRange(start = start, end = end)
        transactions = generator.generate(time_range = time_range, account_pool_size = 50000)
    else:
        logger.info('Running custom generation (%d txns)...', args.count)
        factory = AccountFactory(seed_manager)
        factory.generate_account_pool(size = args.accounts)
        gen = TransactionGenerator(seed_manager, factory)
        end = datetime.now()
        start = end - timedelta(days = 30)
        transactions = gen.generate_batch(count = args.count, time_range = TimeRange(start, end))
    logger.info('Computing statistics...')
    collector = StatsCollector()
    stats = collector.compute(transactions)
    output_stats_text(stats, out_dir / 'stats.txt')
    output_stats_json(stats, out_dir / 'stats.json')
    file_path = out_dir / f'''transactions.{args.format}'''
    logger.info('Writing to file: %s', file_path)
    file_writer = FileWriter(file_path, format = args.format)
    file_writer.write(transactions)
    file_writer.close()
    if args.kafka:
        logger.info('Streaming to Kafka (%s -> %s) at %d TPS...', args.kafka_brokers, args.kafka_topic, args.kafka_tps)
        kafka_writer = KafkaWriter(bootstrap_servers = args.kafka_brokers, topic = args.kafka_topic, rate_per_sec = args.kafka_tps)
        kafka_writer.write(transactions)
        kafka_writer.close()
    logger.info('Generation complete!')
    return 0

if __name__ == '__main__':
    sys.exit(main())
